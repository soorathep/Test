#!/usr/bin/env python
"""
cellpose_sem_count.py
Count and size particles in an SEM micrograph.

Cellpose-SAM segments the particles without any training, scikit-image turns the
masks into measurements, and a shape filter keeps only the particles you mean.

Install the requirements once
    pip install cellpose scikit-image pandas matplotlib

Then run
    python cellpose_sem_count.py micrograph.tif \
        --pixel-size 4.88 --crop-bottom 60 --min-circularity 0.7

Outputs, written next to the image
    <stem>_particles.csv   one row per particle
    <stem>_analysis.pdf    outline overlay and size distribution
    <stem>_analysis.png    the same figure at 600 dpi

The first run downloads the Cellpose-SAM model weights, so it needs a network
connection and takes longer than later runs. A GPU is used automatically when one is
available; pass --cpu to force the processor.

Tested with cellpose 4.2.1 (Cellpose-SAM).
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cellpose import models, utils
from skimage import io, measure
from skimage.color import rgb2gray

try:
    import skh_palette as skh
    skh.use()
    C = skh.C
except ImportError:  # palette not installed: fall back to plain matplotlib
    skh = None
    C = {"teal": "#0F6E6B", "amber": "#E29A2D", "graphite": "#333F4A",
         "slate": "#66727C", "sand": "#DFC98F"}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image", type=Path, help="SEM micrograph (tif, png, jpg)")
    p.add_argument("--pixel-size", type=float, required=True,
                   help="nanometres per pixel, read from the instrument or the scale bar")
    p.add_argument("--crop-bottom", type=int, default=0,
                   help="rows to remove from the bottom, for the instrument info banner")
    p.add_argument("--diameter", type=float, default=None,
                   help="expected particle diameter in pixels; leave unset to let the model decide")
    p.add_argument("--min-area", type=float, default=50.0,
                   help="discard objects smaller than this area in pixels")
    p.add_argument("--min-circularity", type=float, default=0.0,
                   help="keep only particles at or above this circularity, 1.0 being a perfect disc")
    p.add_argument("--flow-threshold", type=float, default=0.4)
    p.add_argument("--cellprob-threshold", type=float, default=0.0)
    p.add_argument("--cpu", action="store_true", help="force CPU instead of the Apple GPU")
    return p.parse_args()


def load_grayscale(path, crop_bottom):
    """Read the micrograph, drop the instrument banner, return a 2-D float array."""
    img = io.imread(path)
    if img.ndim == 3:
        img = rgb2gray(img[..., :3])
    if crop_bottom > 0:
        img = img[:-crop_bottom, :]
    img = img.astype(float)
    rng = img.max() - img.min()
    return (img - img.min()) / rng if rng > 0 else img


def segment(img, args):
    """Run Cellpose-SAM and return the integer label image."""
    model = models.CellposeModel(gpu=not args.cpu)
    masks, _flows, _styles = model.eval(
        img,
        diameter=args.diameter,
        flow_threshold=args.flow_threshold,
        cellprob_threshold=args.cellprob_threshold,
    )
    return masks


def measure_particles(masks, pixel_size_nm, min_area, min_circularity):
    """One row per particle, in nanometres. Circularity is 4 pi A / P^2."""
    props = measure.regionprops_table(
        masks,
        properties=("label", "area", "perimeter", "equivalent_diameter_area",
                    "major_axis_length", "minor_axis_length",
                    "eccentricity", "solidity", "centroid"),
    )
    df = pd.DataFrame(props)
    df = df[df["area"] >= min_area].copy()

    perim = df["perimeter"].replace(0, np.nan)
    df["circularity"] = 4.0 * np.pi * df["area"] / perim**2
    df["aspect_ratio"] = df["major_axis_length"] / df["minor_axis_length"].replace(0, np.nan)

    # Convert to physical units. Area scales with the square of the pixel size.
    px = pixel_size_nm
    df["area_nm2"] = df["area"] * px**2
    for col in ("equivalent_diameter_area", "major_axis_length", "minor_axis_length", "perimeter"):
        df[col + "_nm"] = df[col] * px

    if min_circularity > 0:
        df = df[df["circularity"] >= min_circularity]

    return df.reset_index(drop=True)


def make_figure(img, masks, df, stem, pixel_size_nm):
    """Left: outlines over the micrograph. Right: size distribution."""
    fig, (ax_img, ax_hist) = plt.subplots(
        1, 2, figsize=(6.93, 2.9), gridspec_kw={"width_ratios": [1.1, 1]}
    )

    ax_img.imshow(img, cmap="gray")
    for outline in utils.outlines_list(masks):
        ax_img.plot(outline[:, 0], outline[:, 1], color=C["amber"], linewidth=0.8)
    ax_img.set_xticks([])
    ax_img.set_yticks([])
    ax_img.grid(False)
    ax_img.set_title(f"{len(df)} particles")

    d = df["equivalent_diameter_area_nm"].dropna()
    ax_hist.hist(d, bins=20, color=C["teal"], edgecolor="white", linewidth=0.5)
    ax_hist.axvline(d.mean(), color=C["graphite"], linewidth=1.0, linestyle=(0, (4, 3)))
    ax_hist.set_xlabel("Equivalent diameter / nm")
    ax_hist.set_ylabel("Count")
    ax_hist.set_title(f"mean {d.mean():.0f} nm, SD {d.std():.0f} nm")

    fig.savefig(f"{stem}_analysis.pdf", bbox_inches="tight")
    fig.savefig(f"{stem}_analysis.png", dpi=600, bbox_inches="tight")
    return fig


def main():
    args = parse_args()
    stem = str(args.image.with_suffix(""))

    img = load_grayscale(args.image, args.crop_bottom)
    masks = segment(img, args)
    df = measure_particles(masks, args.pixel_size, args.min_area, args.min_circularity)

    df.to_csv(f"{stem}_particles.csv", index=False)
    make_figure(img, masks, df, stem, args.pixel_size)

    d = df["equivalent_diameter_area_nm"]
    print(f"particles kept      : {len(df)}")
    print(f"equivalent diameter : {d.mean():.1f} +/- {d.std():.1f} nm")
    print(f"circularity         : {df['circularity'].mean():.2f}")
    print(f"written             : {stem}_particles.csv, {stem}_analysis.pdf/.png")


if __name__ == "__main__":
    main()
