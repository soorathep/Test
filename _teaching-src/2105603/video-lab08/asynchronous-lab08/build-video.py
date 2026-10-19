"""Compose and verify the Lab 08 demonstration from actual screenshots and PCM.

Run with ~/.venvs/research/bin/python asynchronous-lab08/build-video.py.
Use --prepare-only to inspect frames before encoding, or --validate-only to
verify an existing video. No screenshots or speech are generated here.

The audio timeline owns all chapter boundaries. Scene fractions partition each
chapter; rounding to integer PCM samples happens once, before encoding. Relative
image paths resolve against the workspace root, then the scenes file's folder.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import heapq
import json
import math
import os
from pathlib import Path
import struct
import time

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
import soundfile as sf
from scipy.signal import correlate, correlation_lags, resample_poly


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "outputs/lab08-video"
WIDTH, HEIGHT, RATE = 1920, 1080, 24000
TB = Fraction(1, RATE)
PANEL = (48, 132, 1872, 958)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path):
    path = Path(path).resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_path(value, base=ROOT):
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def palette():
    # skh_palette imports matplotlib; keep its cache in the writable workspace.
    cache = ROOT / "tmp/video/lab08/matplotlib"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache))
    os.environ.setdefault("MPLBACKEND", "Agg")
    import skh_palette as skh
    skh.use()
    return skh.C


def font(size, bold=False):
    names = [
        Path("/System/Library/Fonts/Supplemental") / ("Arial Bold.ttf" if bold else "Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu") / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
    ]
    for path in names:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def text_lines(draw, text, face, width):
    lines, current = [], ""
    for word in str(text).split():
        candidate = f"{current} {word}".strip()
        if current and draw.textlength(candidate, font=face) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    require(all(draw.textlength(line, font=face) <= width for line in lines),
            "An unbroken label exceeds the available frame width")
    return lines


def compose(source, crop, chapter, label, colors):
    with Image.open(source) as original:
        screenshot = ImageOps.exif_transpose(original).convert("RGB")
    original_size = list(screenshot.size)
    if crop is not None:
        require(isinstance(crop, list) and len(crop) == 4 and
                all(isinstance(x, int) and not isinstance(x, bool) for x in crop),
                f"Crop must contain four integer pixels: {source}")
        left, top, right, bottom = crop
        require(0 <= left < right <= screenshot.width and
                0 <= top < bottom <= screenshot.height,
                f"Crop lies outside source image {source}: {crop}")
        screenshot = screenshot.crop(tuple(crop))
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, WIDTH, 7), fill=colors["teal"])
    draw.text((48, 22), "LAB 08  |  FROM EXPERIMENTAL DATA TO MODEL FITTING",
              font=font(22, True), fill=colors["teal"])
    chapter_label = f"CHAPTER {chapter['id']} / 14"
    draw.text((1872, 22), chapter_label, font=font(22),
              fill=colors["graphite"], anchor="ra")
    title_face = font(42, True)
    while draw.textlength(chapter["title"], font=title_face) > 1824 and title_face.size > 28:
        title_face = font(title_face.size - 1, True)
    require(draw.textlength(chapter["title"], font=title_face) <= 1824,
            f"Chapter title is too long: {chapter['title']}")
    draw.text((48, 62), chapter["title"], font=title_face, fill=colors["graphite"])
    left, top, right, bottom = PANEL
    content = ImageOps.contain(screenshot, (right - left - 4, bottom - top - 4),
                               method=Image.Resampling.LANCZOS)
    x = left + (right - left - content.width) // 2
    y = top + (bottom - top - content.height) // 2
    canvas.paste(content, (x, y))
    draw.rectangle(PANEL, outline=colors["mist"], width=2)
    label_face = font(29)
    lines = text_lines(draw, label, label_face, 1772)
    require(len(lines) <= 2, f"Scene label needs more than two lines: {label}")
    draw.rectangle((48, 978, 55, 1035), fill=colors["amber"])
    for index, line in enumerate(lines):
        draw.text((72, 973 + index * 33), line, font=label_face, fill=colors["graphite"])
    draw.text((48, 1049), "2105603 Advanced Thermodynamics", font=font(18), fill=colors["slate"])
    draw.text((1872, 1049), "Pause the video to try each step.", font=font(18),
              fill=colors["slate"], anchor="ra")
    return canvas, {"source_dimensions": original_size, "cropped_dimensions": list(screenshot.size),
                    "display_rectangle": [x, y, x + content.width, y + content.height],
                    "display_scale": content.width / screenshot.width}


def prepare(args):
    audio_path, scenes_path, master = args.audio_timeline, args.scenes, args.master
    audio = json.loads(audio_path.read_text())
    scene_specs = json.loads(scenes_path.read_text())
    require(isinstance(scene_specs, list) and scene_specs, "scenes.json must be a nonempty list")
    require(audio.get("sample_rate") == RATE, "Expected a 24 kHz audio timeline")
    chapters = audio.get("chapters", [])
    require([c.get("id") for c in chapters] == [f"{n:02}" for n in range(1, 15)],
            "Audio must contain chapters 01 through 14 in order")
    info = sf.info(master)
    require(info.samplerate == RATE and info.channels == 1 and info.subtype == "PCM_16",
            "Master must be mono, 24 kHz, PCM_16 WAV")
    require(info.frames == audio.get("duration_samples") and info.frames > 0,
            "Master length differs from the audio timeline")
    position = 0
    for chapter in chapters:
        require(isinstance(chapter["start_sample"], int) and isinstance(chapter["end_sample"], int),
                "Chapter boundaries must be integer PCM samples")
        require(chapter["start_sample"] == position < chapter["end_sample"],
                f"Noncontiguous or empty chapter {chapter['id']}")
        chapter["start_seconds"] = chapter["start_sample"] / RATE
        chapter["end_seconds"] = chapter["end_sample"] / RATE
        position = chapter["end_sample"]
    require(position == info.frames, "Chapters do not cover the entire PCM master")
    require(all(s.get("chapter_id") in {c["id"] for c in chapters} for s in scene_specs),
            "A scene refers to an unknown chapter")
    require([s["chapter_id"] for s in scene_specs] == sorted(s["chapter_id"] for s in scene_specs),
            "Scene chapters must be in chronological order")
    args.out.mkdir(parents=True, exist_ok=True)
    frames = args.out / "frames"
    frames.mkdir(exist_ok=True)
    colors, scenes = palette(), []
    for chapter in chapters:
        specifications = [s for s in scene_specs if s["chapter_id"] == chapter["id"]]
        require(len(specifications) >= 2, f"Chapter {chapter['id']} needs at least two actual screen views")
        previous_fraction = Fraction(0)
        span = chapter["end_sample"] - chapter["start_sample"]
        for index, spec in enumerate(specifications, 1):
            start_fraction = Fraction(str(spec["start_fraction"]))
            end_fraction = Fraction(str(spec["end_fraction"]))
            require(0 <= start_fraction < end_fraction <= 1, "Scene fractions must satisfy 0 <= start < end <= 1")
            require(abs(start_fraction - previous_fraction) <= Fraction(1, 10**9),
                    f"Gap or overlap between scenes in chapter {chapter['id']}")
            # Use the preceding boundary once, so a tiny decimal representation
            # difference cannot create a one-sample hole at a scene transition.
            start = scenes[-1]["end_sample"] if index > 1 else chapter["start_sample"]
            end = chapter["start_sample"] + round(end_fraction * span)
            require(end > start, "A scene has no duration after sample rounding")
            image_path = resolve_path(spec["image"])
            if not image_path.exists() and not Path(spec["image"]).is_absolute():
                image_path = resolve_path(spec["image"], scenes_path.parent)
            require(image_path.is_file(), f"Screenshot missing: {image_path}")
            label = str(spec.get("label", "")).strip()
            require(label, "Every screenshot needs a short English label")
            frame, geometry = compose(image_path, spec.get("crop"), chapter, label, colors)
            frame_path = frames / f"chapter-{chapter['id']}-view-{index:02}.jpg"
            frame.save(frame_path, quality=97, subsampling=0)
            scenes.append({"scene_id": f"{chapter['id']}-{index:02}", "chapter_id": chapter["id"],
                           "label": label, "start_sample": start, "end_sample": end,
                           "start_seconds": start / RATE, "end_seconds": end / RATE,
                           "source_image": display_path(image_path), "source_image_sha256": sha(image_path),
                           "crop": spec.get("crop"), "frame_image": display_path(frame_path),
                           "frame_image_sha256": sha(frame_path), **geometry})
            previous_fraction = end_fraction
        require(previous_fraction == 1 and scenes[-1]["end_sample"] == chapter["end_sample"],
                f"Scenes do not cover the end of chapter {chapter['id']}")
    Image.open(resolve_path(scenes[0]["frame_image"])).save(args.out / "poster.jpg", quality=95, subsampling=0)
    timeline = {"title": "Lab 08: From VLE data to activity model fitting",
                "video": "lab08-demo.mp4", "poster": "poster.jpg", "width": WIDTH, "height": HEIGHT,
                "sample_rate": RATE, "time_base": "1/24000", "duration_samples": info.frames,
                "duration_seconds": info.frames / RATE, "chapters": chapters, "scenes": scenes,
                "cues": audio.get("cues", []), "audio_master": display_path(master),
                "audio_master_sha256": sha(master), "source_audio_timeline": display_path(audio_path),
                "source_audio_timeline_sha256": sha(audio_path), "source_scenes": display_path(scenes_path),
                "source_scenes_sha256": sha(scenes_path), "crf": args.crf,
                "maximum_size_bytes": round(args.max_mb * 1_000_000),
                "timing_contract": "The unchanged PCM master determines exact chapter boundaries. Actual screenshot scenes partition each chapter continuously. Pause playback for practice.",
                "frame_provenance": "Actual supplied screenshots, cropped only as specified, scaled with preserved aspect ratio, with a separate title and instructional footer."}
    write_json(args.out / "timeline.json", timeline)
    create_contact_sheet(timeline, args.out / "contact-sheet.jpg", colors)
    print(f"Prepared {len(scenes)} screenshot views in 14 chapters; {info.frames / RATE:.3f} seconds", flush=True)
    return timeline


def create_contact_sheet(timeline, path, colors, decoded=None):
    scenes = timeline["scenes"]
    contact = Image.new("RGB", (4 * 480, math.ceil(len(scenes) / 4) * 315), "white")
    draw = ImageDraw.Draw(contact)
    for index, scene in enumerate(scenes):
        if decoded is not None:
            small = decoded[scene["scene_id"]]
        else:
            with Image.open(resolve_path(scene["frame_image"])) as image:
                small = image.resize((480, 270), Image.Resampling.LANCZOS)
        x, y = index % 4 * 480, index // 4 * 315
        contact.paste(small, (x, y))
        draw.text((x + 10, y + 276), f"View {scene['scene_id']}  |  {scene['start_seconds']:.3f} s",
                  font=font(19), fill=colors["graphite"])
    contact.save(path, quality=94, subsampling=0)


def encode(timeline, out):
    started = time.monotonic()
    destination = out / timeline["video"]
    temporary = destination.with_suffix(".partial.mp4")
    with av.open(str(temporary), "w", format="mp4", options={"movflags": "+faststart"}) as output:
        video = output.add_stream("libx264", rate=30)
        video.width, video.height, video.pix_fmt = WIDTH, HEIGHT, "yuv420p"
        video.time_base = video.codec_context.time_base = TB
        video.codec_context.thread_count = 4
        video.codec_context.gop_size = 5
        video.codec_context.max_b_frames = 0
        video.options = {"crf": str(timeline["crf"]), "preset": "veryfast", "tune": "stillimage,zerolatency"}
        sound = output.add_stream("aac", rate=48000)
        sound.layout, sound.bit_rate, sound.time_base = "mono", 128000, Fraction(1, 48000)
        output.metadata.update(title=timeline["title"], artist="Soorathep Kheawhom",
                               comment="Actual Lab screenshots with English synthetic male narration. Pause for practice.")
        output.set_chapters([{"id": int(c["id"]), "start": c["start_sample"], "end": c["end_sample"],
                              "time_base": TB, "metadata": {"title": f"{c['id']}. {c['title']}"}}
                             for c in timeline["chapters"]])

        def video_packets():
            for scene in timeline["scenes"]:
                with Image.open(resolve_path(scene["frame_image"])) as image:
                    frame = av.VideoFrame.from_image(image.convert("RGB")).reformat(format="yuv420p")
                for pts in range(scene["start_sample"], scene["end_sample"], RATE):
                    duration = min(RATE, scene["end_sample"] - pts)
                    frame.pts, frame.time_base, frame.duration = pts, TB, duration
                    frame.pict_type = av.video.frame.PictureType.I if pts == scene["start_sample"] else av.video.frame.PictureType.NONE
                    for packet in video.encode(frame):
                        require(packet.pts == pts and packet.time_base == TB,
                                "Encoder delayed/reordered a frame; keep zero latency and B-frames disabled")
                        packet.duration = duration
                        yield packet
                print(f"Encoded view {scene['scene_id']} ({time.monotonic() - started:.1f} s)", flush=True)
            yield from video.encode(None)

        def audio_packets():
            resampler = av.AudioResampler(format="fltp", layout="mono", rate=48000)
            with sf.SoundFile(resolve_path(timeline["audio_master"])) as source:
                pos = 0
                while pos < timeline["duration_samples"]:
                    data = source.read(min(12000, timeline["duration_samples"] - pos), dtype="int16")
                    require(len(data) > 0, "Unexpected end of PCM master")
                    frame = av.AudioFrame.from_ndarray(data.reshape(1, -1), format="s16", layout="mono")
                    frame.sample_rate, frame.time_base, frame.pts = RATE, TB, pos
                    pos += len(data)
                    for converted in resampler.resample(frame):
                        yield from sound.encode(converted)
                for converted in resampler.resample(None):
                    yield from sound.encode(converted)
                yield from sound.encode(None)

        generators = [iter(video_packets()), iter(audio_packets())]
        heap = []
        for index, generator in enumerate(generators):
            packet = next(generator, None)
            if packet is not None:
                heapq.heappush(heap, (packet.dts * packet.time_base, index, packet))
        while heap:
            _, index, packet = heapq.heappop(heap)
            output.mux(packet)
            following = next(generators[index], None)
            if following is not None:
                heapq.heappush(heap, (following.dts * following.time_base, index, following))
    temporary.replace(destination)
    timeline.update(video_sha256=sha(destination), video_size_bytes=destination.stat().st_size,
                    encoding_wall_seconds=round(time.monotonic() - started, 2))
    write_json(out / "timeline.json", timeline)


def mp4_atoms(path):
    atoms, total = {}, path.stat().st_size
    with path.open("rb") as source:
        while source.tell() < total:
            start = source.tell()
            header = source.read(8)
            require(len(header) == 8, "Truncated MP4 atom header")
            length, kind = struct.unpack(">I4s", header)
            minimum = 8
            if length == 1:
                extended = source.read(8)
                require(len(extended) == 8, "Truncated extended MP4 atom")
                length, minimum = struct.unpack(">Q", extended)[0], 16
            elif length == 0:
                length = total - start
            require(minimum <= length <= total - start, "Invalid MP4 atom length")
            atoms.setdefault(kind.decode("ascii"), start)
            source.seek(start + length)
    return atoms


def psnr(actual, expected):
    error = float(np.mean((actual.astype("float32") - expected.astype("float32")) ** 2))
    return float(10 * np.log10(255**2 / max(error, 1e-9)))


def audio_sync_check(video_path, master, chapter):
    # Choose a non-silent window from each requested chapter, rather than trusting
    # a timestamp that might fall inside a pedagogical pause.
    with sf.SoundFile(master) as source:
        source.seek(chapter["start_sample"])
        data = source.read(chapter["end_sample"] - chapter["start_sample"], dtype="float32")
    length = min(5 * RATE, len(data))
    require(length >= RATE, "Chapter too short for an audio synchronization check")
    candidates = list(range(0, len(data) - length + 1, RATE))
    offset = max(candidates, key=lambda x: float(np.dot(data[x:x + length], data[x:x + length])))
    expected = data[offset:offset + length]
    require(float(np.sqrt(np.mean(expected**2))) > .001, f"Silent narration in chapter {chapter['id']}")
    start = chapter["start_sample"] + offset
    target, needed = start * 2, length * 2
    with av.open(str(video_path)) as media:
        stream = media.streams.audio[0]
        seek_seconds = max(0, (target - 48000) / 48000)
        media.seek(int(Fraction(str(seek_seconds)) / stream.time_base), stream=stream, backward=True)
        chunks, first, previous_end = [], None, None
        for frame in media.decode(audio=0):
            sample = round(frame.pts * frame.time_base * 48000)
            if first is None:
                first = sample
            require(previous_end is None or sample == previous_end, "Decoded AAC contains a timestamp gap")
            previous_end = sample + frame.samples
            chunks.append(frame.to_ndarray().reshape(-1))
            if previous_end >= target + needed:
                break
        require(first is not None and first <= target, "AAC seek skipped the requested comparison window")
        raw = np.concatenate(chunks)
        local = target - first
        decoded = resample_poly(raw[local:local + needed], 1, 2)
    require(len(decoded) == len(expected), "AAC comparison window is truncated")
    correlation = correlate(decoded, expected, method="fft")
    lag = int(correlation_lags(len(decoded), len(expected))[np.argmax(correlation)])
    coefficient = float(np.corrcoef(decoded, expected)[0, 1])
    require(abs(lag) <= 1 and coefficient > .985,
            f"AAC does not match PCM at chapter {chapter['id']}: lag {lag}, r={coefficient}")
    return {"chapter_id": chapter["id"], "at_seconds": start / RATE,
            "delay_samples_at_24khz": lag, "correlation": round(coefficient, 6)}


def validate(timeline, out):
    video_path, master = out / timeline["video"], resolve_path(timeline["audio_master"])
    require(sha(master) == timeline["audio_master_sha256"], "PCM master changed")
    require(sha(video_path) == timeline["video_sha256"], "Video changed after encoding")
    for path_key in ("source_audio_timeline", "source_scenes"):
        require(sha(resolve_path(timeline[path_key])) == timeline[path_key + "_sha256"], f"{path_key} changed")
    for scene in timeline["scenes"]:
        for path_key in ("source_image", "frame_image"):
            require(sha(resolve_path(scene[path_key])) == scene[path_key + "_sha256"],
                    f"Image changed: {scene[path_key]}")
    info = sf.info(master)
    require(info.frames == timeline["duration_samples"] and info.samplerate == RATE and info.channels == 1,
            "PCM master format or duration changed")
    with sf.SoundFile(master) as source:
        chapter_audio = []
        for chapter in timeline["chapters"]:
            source.seek(chapter["start_sample"])
            samples = source.read(chapter["end_sample"] - chapter["start_sample"], dtype="float32")
            peak, rms = float(np.max(np.abs(samples))), float(np.sqrt(np.mean(samples**2)))
            require(peak > .02 and rms > .001, f"Chapter {chapter['id']} has no useful audio")
            chapter_audio.append({"chapter_id": chapter["id"], "rms": round(rms, 6), "peak": round(peak, 6)})
    atoms = mp4_atoms(video_path)
    require("moov" in atoms and "mdat" in atoms and atoms["moov"] < atoms["mdat"], "MP4 is not faststart")
    require(0 < video_path.stat().st_size <= timeline["maximum_size_bytes"],
            f"Video exceeds size budget: {video_path.stat().st_size / 1e6:.2f} MB; consider --crf 20")
    scenes, transitions, thumbnails = timeline["scenes"], [], {}
    scene_index, previous_end, frames = 0, 0, 0
    expected, first_score = None, None
    with av.open(str(video_path)) as media:
        require(abs(media.duration / 1e6 - timeline["duration_seconds"]) <= .001, "MP4 duration differs from PCM")
        require(len(media.streams.video) == 1 and len(media.streams.audio) == 1, "Expected one video and one audio stream")
        video, sound = media.streams.video[0], media.streams.audio[0]
        require((video.width, video.height, video.codec_context.name, video.codec_context.pix_fmt) ==
                (WIDTH, HEIGHT, "h264", "yuv420p"), "Unexpected video codec or dimensions")
        require(sound.codec_context.name == "aac" and sound.codec_context.sample_rate == 48000 and
                sound.codec_context.layout.name == "mono", "Unexpected audio format")
        require(video.start_time == sound.start_time == 0, "Stream starts are not zero")
        chapters = media.chapters()
        require(len(chapters) == 14, "Expected 14 embedded chapters")
        for actual, planned in zip(chapters, timeline["chapters"]):
            for boundary in ("start", "end"):
                require(abs(float(actual[boundary] * actual["time_base"]) - planned[boundary + "_seconds"]) < .001,
                        f"Chapter {planned['id']} boundary differs from PCM")
            require(actual["metadata"].get("title") == f"{planned['id']}. {planned['title']}", "Chapter title differs")
        for frame in media.decode(video=0):
            sample = round(frame.pts * frame.time_base * RATE)
            duration = round(frame.duration * frame.time_base * RATE)
            require(sample == previous_end and duration > 0, "Video has a gap, overlap, or zero-duration frame")
            while scene_index + 1 < len(scenes) and sample >= scenes[scene_index]["end_sample"]:
                scene_index += 1
            scene = scenes[scene_index]
            require(sample + duration <= scene["end_sample"], "A video frame crosses its screenshot boundary")
            if sample == scene["start_sample"]:
                require(frame.key_frame, "Screenshot boundary is not a keyframe")
                with Image.open(resolve_path(scene["frame_image"])) as image:
                    expected = np.asarray(image.convert("RGB"))
                actual = frame.to_ndarray(format="rgb24")
                first_score = psnr(actual, expected)
                require(first_score > 33, f"Screenshot quality too low at {scene['scene_id']}: {first_score:.2f} dB")
                thumbnails[scene["scene_id"]] = Image.fromarray(actual).resize((480, 270), Image.Resampling.LANCZOS)
            if sample + duration == scene["end_sample"]:
                last_score = psnr(frame.to_ndarray(format="rgb24"), expected)
                require(last_score > 33, f"Screenshot changed early at {scene['scene_id']}")
                transitions.append({"scene_id": scene["scene_id"], "start_sample": scene["start_sample"],
                                    "end_sample": scene["end_sample"], "first_frame_keyframe": True,
                                    "first_frame_psnr_db": round(first_score, 2), "last_frame_psnr_db": round(last_score, 2)})
            previous_end, frames = sample + duration, frames + 1
        require(previous_end == timeline["duration_samples"] and len(transitions) == len(scenes),
                "Decoded frames do not cover every scene and the full audio duration")
    checks = [audio_sync_check(video_path, master, timeline["chapters"][index]) for index in (0, 7, 13)]
    create_contact_sheet(timeline, out / "contact-sheet.jpg", palette(), thumbnails)
    report = {"passed": True, "video": timeline["video"], "video_sha256": sha(video_path),
              "size_bytes": video_path.stat().st_size, "maximum_size_bytes": timeline["maximum_size_bytes"],
              "duration_seconds": timeline["duration_seconds"], "duration_samples": timeline["duration_samples"],
              "dimensions": [WIDTH, HEIGHT], "video_codec": "h264", "pixel_format": "yuv420p",
              "audio_codec": "aac", "audio_channels": 1, "audio_sample_rate": 48000,
              "timeline_sample_rate": RATE, "chapter_count": 14, "screenshot_count": len(scenes),
              "faststart": True, "source_hashes_verified": True, "pcm_master_unchanged": True,
              "all_frame_boundaries_contiguous": True, "no_early_screenshot_switches": True,
              "decoded_video_frames": frames, "scene_checks": transitions, "chapter_audio_checks": chapter_audio,
              "audio_sync_checks": checks, "full_subjective_listening_review_performed": False,
              "screenshot_readability_review_performed": False}
    write_json(out / "video-qa.json", report)
    print(json.dumps({"passed": True, "file": str(video_path), "seconds": timeline["duration_seconds"],
                      "megabytes": video_path.stat().st_size / 1e6, "chapters": 14, "screenshots": len(scenes),
                      "minimum_scene_psnr_db": min(r["first_frame_psnr_db"] for r in transitions),
                      "audio_sync_checks": checks}), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenes", type=Path, default=ROOT / "asynchronous-lab08/scenes.json")
    parser.add_argument("--audio-timeline", type=Path, default=DEFAULT_OUT / "audio/timeline.json")
    parser.add_argument("--master", type=Path, default=DEFAULT_OUT / "audio/master.wav")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--max-mb", type=float, default=80)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    require(0 <= args.crf <= 35 and args.max_mb > 0, "Invalid CRF or file-size budget")
    for name in ("scenes", "audio_timeline", "master", "out"):
        setattr(args, name, resolve_path(getattr(args, name)))
    qa = args.out / "video-qa.json"
    try:
        if args.validate_only:
            plan = json.loads((args.out / "timeline.json").read_text())
        else:
            plan = prepare(args)
            # A prior success report must never describe newly prepared frames.
            if qa.exists():
                qa.unlink()
            if args.prepare_only:
                return
            encode(plan, args.out)
        validate(plan, args.out)
    except Exception as error:
        if args.out.exists():
            write_json(qa, {"passed": False, "error": str(error), "error_type": type(error).__name__})
        raise


if __name__ == "__main__":
    main()
