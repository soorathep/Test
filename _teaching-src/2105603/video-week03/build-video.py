"""Build and verify the 31-slide Session 3 video from audited PDF and PCM audio.

Run with ~/.venvs/research/bin/python asynchronous-week03/build-video.py.
No slide content or speech is regenerated. Each slide receives a two-second
silent tail. Integer 24 kHz sample positions govern every transition.
"""
from pathlib import Path
from fractions import Fraction
import argparse
import csv
import hashlib
import heapq
import json
import math
import os
import struct
import time

import av
import numpy as np
import pymupdf
import soundfile as sf
from PIL import Image, ImageDraw
from scipy.signal import correlate, correlation_lags, resample_poly

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "output/pdf/postmidterm-03-slides.pdf"
MANIFEST = ROOT / "outputs/week03-video/audio/manifest.json"
WAVS = ROOT / "outputs/week03-video/audio"
WORK = ROOT / "tmp/video/week03"
IMAGES = WORK / "slides"
OUT = ROOT / "outputs/week03-video"
VIDEO = OUT / "week03-lecture.mp4"
MASTER = WORK / "audio-master.wav"
RATE = 24000
TB = Fraction(1, RATE)
TAIL = 2 * RATE
WIDTH, HEIGHT = 1920, 1080
SLIDE_HEIGHT = 920
EXPECTED_PDF_SHA256 = "c07fd0b99e7703dc386db1d393922e0fa3d824240ce9e60657429baccda9770c"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare():
    for directory in (WORK, IMAGES, OUT):
        directory.mkdir(parents=True, exist_ok=True)
    entries = json.loads(MANIFEST.read_text())
    os.environ.setdefault('MPLCONFIGDIR',str(WORK/'matplotlib'))
    import skh_palette as skh
    skh.use()
    assert [e["slide"] for e in entries] == list(range(1, 32))
    pdf_hash = sha(PDF)
    assert pdf_hash == EXPECTED_PDF_SHA256, 'The audited slide PDF changed; review and freeze it before rebuilding.'
    rows, offset = [], 0
    with pymupdf.open(PDF) as document, sf.SoundFile(
        MASTER, "w", samplerate=RATE, channels=1, subtype="PCM_16"
    ) as master:
        assert len(document) == 31
        for entry, page in zip(entries, document):
            n = entry["slide"]
            source = WAVS / f"segment-{n:02}.wav"
            samples, rate = sf.read(source, dtype="int16")
            assert rate == RATE and samples.ndim == 1
            assert abs(len(samples) / RATE - entry["duration_seconds"]) <= 0.0051
            assert entry["generation"]["voice"] == "am_michael"
            assert entry["generation"]["speed"] == 0.94
            master.write(samples)
            master.write(np.zeros(TAIL, dtype=np.int16))
            # Preserve the entire slide and reserve a separate caption band.
            scale = min(WIDTH / page.rect.width, SLIDE_HEIGHT / page.rect.height)
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            assert image.width <= WIDTH and image.height <= HEIGHT
            canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
            canvas.paste(image, ((WIDTH - image.width) // 2, (SLIDE_HEIGHT - image.height) // 2))
            ImageDraw.Draw(canvas).rectangle((0,SLIDE_HEIGHT,WIDTH,HEIGHT),fill=skh.C['graphite'])
            image_path = IMAGES / f"slide-{n:02}.png"
            canvas.save(image_path)
            end = offset + len(samples) + TAIL
            rows.append({
                "slide": n, "title": entry["title"],
                "start_sample": offset, "narration_end_sample": offset + len(samples),
                "end_sample": end, "narration_samples": len(samples),
                "start_seconds": offset / RATE,
                "narration_end_seconds": (offset + len(samples)) / RATE,
                "end_seconds": end / RATE,
                "narration_duration_seconds": len(samples) / RATE,
                "silent_tail_seconds": TAIL / RATE,
                "pause_instruction": entry["pause_instruction"],
                "activity": entry["activity"],
                "activity_minutes": entry.get("activity_minutes", 0),
                "slide_id": entry["slide_id"],
                "stage_start_minute": entry["stage_start_minute"],
                "stage_end_minute": entry["stage_end_minute"],
                "audio_source": str(source.relative_to(ROOT)),
                "audio_source_sha256": sha(source),
                "slide_image": str(image_path.relative_to(ROOT)),
                "slide_image_sha256": sha(image_path),
                "pdf_source_sha256": pdf_hash,
                "narration_text_sha256": hashlib.sha256(entry["narration"].encode()).hexdigest(),
            })
            offset = end
    Image.open(IMAGES / "slide-01.png").save(OUT / "week03-poster.png")
    timeline = {
        "title": "Week 3: Thermodynamic consistency and liquid stability",
        "video": VIDEO.name, "poster": "week03-poster.png",
        "width": WIDTH, "height": HEIGHT, "sample_rate": RATE,
        "slide_height": SLIDE_HEIGHT, "caption_band_height": HEIGHT-SLIDE_HEIGHT,
        "time_base": "1/24000", "silent_tail_per_slide_seconds": 2,
        "duration_samples": offset, "duration_seconds": offset / RATE,
        "narration_duration_seconds": sum(r["narration_samples"] for r in rows) / RATE,
        "lesson_working_time_minutes": 180,
        "timing_contract": "Slide starts at its PCM audio start. It remains visible throughout the exact WAV duration and a 2-second silent tail. Pause playback for calculation and Lab activities; the video contains no exercise-length filler silence.",
        "source_pdf": str(PDF.relative_to(ROOT)), "source_pdf_sha256": pdf_hash,
        "source_manifest": str(MANIFEST.relative_to(ROOT)), "source_manifest_sha256": sha(MANIFEST),
        "audio_master_sha256": sha(MASTER), "slides": rows,
    }
    (OUT / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n")
    with (OUT / "timeline.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    audio_timeline=json.loads((WAVS/'timeline.json').read_text())
    cues=[]
    for original in audio_timeline['cues']:
        cue={**original}; delta=(int(cue['chapter_id'])-1)*TAIL
        cue['start_sample']+=delta;cue['end_sample']+=delta
        cue['start_seconds']=cue['start_sample']/RATE;cue['end_seconds']=cue['end_sample']/RATE
        cues.append(cue)
    def stamp(sample):
        msec=round(sample*1000/RATE);h,rest=divmod(msec,3600000);m,rest=divmod(rest,60000);s,ms=divmod(rest,1000)
        return f'{h:02}:{m:02}:{s:02}.{ms:03}'
    import html,textwrap
    vtt=['WEBVTT','']
    for cue in cues:
        row=rows[int(cue['chapter_id'])-1]
        assert row['start_sample']<=cue['start_sample']<cue['end_sample']<=row['narration_end_sample']
        vtt += [cue['id'],f"{stamp(cue['start_sample'])} --> {stamp(cue['end_sample'])}",'\n'.join(textwrap.wrap(html.escape(cue['text'],quote=False),70,break_long_words=False)), '']
    (OUT/'week03-captions.vtt').write_text('\n'.join(vtt))
    (OUT/'caption-timeline.json').write_text(json.dumps(cues,indent=2)+'\n')
    return timeline


def encode(timeline):
    start = time.monotonic()
    temporary = VIDEO.with_suffix(".partial.mp4")
    with av.open(str(temporary), "w", format="mp4", options={"movflags": "+faststart"}) as output:
        video = output.add_stream("libx264", rate=30)
        video.width, video.height = WIDTH, HEIGHT
        video.pix_fmt = "yuv420p"
        video.time_base = TB
        video.codec_context.time_base = TB
        video.codec_context.thread_count = 4
        video.codec_context.gop_size = 5
        video.codec_context.max_b_frames = 0
        video.options = {"crf": "18", "preset": "veryfast", "tune": "stillimage,zerolatency"}
        sound = output.add_stream("aac", rate=48000)
        sound.layout = "mono"
        sound.bit_rate = 128000
        sound.time_base = Fraction(1, 48000)
        output.metadata.update(
            title=timeline["title"], artist="Soorathep Kheawhom",
            comment="English synthetic male narration. Pause for independent calculations and Lab activities.",
        )
        output.set_chapters([
            {"id": row["slide"], "start": row["start_sample"], "end": row["end_sample"],
             "time_base": TB, "metadata": {"title": f"{row['slide']:02}. {row['title']}"}}
            for row in timeline["slides"]
        ])

        def video_packets():
            for row in timeline["slides"]:
                frame = av.VideoFrame.from_image(Image.open(ROOT / row["slide_image"]).convert("RGB")).reformat(format="yuv420p")
                for pts in range(row["start_sample"], row["end_sample"], RATE):
                    length = min(RATE, row["end_sample"] - pts)
                    frame.pts, frame.time_base, frame.duration = pts, TB, length
                    frame.pict_type = av.video.frame.PictureType.I if pts == row["start_sample"] else av.video.frame.PictureType.NONE
                    for packet in video.encode(frame):
                        assert packet.pts == pts and packet.time_base == TB
                        packet.duration = length
                        yield packet
                print(f"Encoded slide {row['slide']:02}/31 ({time.monotonic() - start:.1f}s)", flush=True)
            yield from video.encode(None)

        def audio_packets():
            resampler = av.AudioResampler(format="fltp", layout="mono", rate=48000)
            with sf.SoundFile(MASTER) as source:
                pos = 0
                while pos < timeline["duration_samples"]:
                    samples = source.read(min(12000, timeline["duration_samples"] - pos), dtype="int16")
                    frame = av.AudioFrame.from_ndarray(samples.reshape(1, -1), format="s16", layout="mono")
                    frame.sample_rate, frame.time_base, frame.pts = RATE, TB, pos
                    pos += len(samples)
                    for converted in resampler.resample(frame):
                        yield from sound.encode(converted)
                for converted in resampler.resample(None):
                    yield from sound.encode(converted)
                yield from sound.encode(None)

        generators = [iter(video_packets()), iter(audio_packets())]
        heap = []
        for n, generator in enumerate(generators):
            try:
                packet = next(generator)
                heapq.heappush(heap, (packet.dts * packet.time_base, n, packet))
            except StopIteration:
                pass
        while heap:
            _, n, packet = heapq.heappop(heap)
            output.mux(packet)
            try:
                packet = next(generators[n])
                heapq.heappush(heap, (packet.dts * packet.time_base, n, packet))
            except StopIteration:
                pass
    temporary.replace(VIDEO)
    assert VIDEO.stat().st_size < 100_000_000, 'Split the recording into parts before Git publication.'
    timeline["video_sha256"] = sha(VIDEO)
    timeline["video_size_bytes"] = VIDEO.stat().st_size
    timeline["encoding_wall_seconds"] = round(time.monotonic() - start, 2)
    (OUT / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n")


def mp4_atoms(path):
    atoms = []
    with path.open("rb") as file:
        while True:
            position = file.tell()
            header = file.read(8)
            if not header:
                break
            length, kind = struct.unpack(">I4s", header)
            if length == 1:
                length = struct.unpack(">Q", file.read(8))[0]
            if length == 0:
                length = path.stat().st_size - position
            atoms.append((kind.decode("ascii"), position))
            file.seek(position + length)
    return atoms


def psnr(actual, expected):
    mse = float(np.mean((actual.astype("float32") - expected.astype("float32")) ** 2))
    return float(10 * np.log10(255 ** 2 / max(mse, 1e-9)))


def validate(timeline):
    rows = timeline["slides"]
    assert sha(PDF) == timeline["source_pdf_sha256"]
    assert sha(MANIFEST) == timeline["source_manifest_sha256"]
    for row in rows:
        assert sha(ROOT / row["audio_source"]) == row["audio_source_sha256"]
        assert sha(ROOT / row["slide_image"]) == row["slide_image_sha256"]
    assert sha(MASTER) == timeline["audio_master_sha256"]
    assert sha(VIDEO) == timeline["video_sha256"]
    # Confirm sample-exact source placement and all 31 silent tails.
    with sf.SoundFile(MASTER) as source:
        assert source.frames == timeline["duration_samples"] and source.samplerate == RATE
        for row in rows:
            source.seek(row["start_sample"])
            actual = source.read(row["narration_samples"], dtype="int16")
            expected, rate = sf.read(ROOT / row["audio_source"], dtype="int16")
            assert np.array_equal(actual, expected)
            assert not np.any(source.read(TAIL, dtype="int16"))
    atoms = dict(mp4_atoms(VIDEO))
    assert atoms["moov"] < atoms["mdat"]
    expected_images = [np.asarray(Image.open(ROOT / r["slide_image"]).convert("RGB")) for r in rows]
    transitions, all_frames, seen = [], 0, set()
    previous_sample, previous_end, previous_image, previous_row = -1, 0, None, None
    contact = Image.new("RGB", (480 * 4, (270 + 30) * 8), "white")
    draw = ImageDraw.Draw(contact)
    with av.open(str(VIDEO)) as media:
        assert abs(media.duration / 1e6 - timeline["duration_seconds"]) <= .001
        video, sound = media.streams.video[0], media.streams.audio[0]
        assert (video.width, video.height, video.codec_context.name, video.codec_context.pix_fmt) == (WIDTH, HEIGHT, "h264", "yuv420p")
        assert sound.codec_context.name == "aac" and sound.codec_context.sample_rate == 48000
        assert sound.codec_context.layout.name == "mono"
        assert video.start_time == sound.start_time == 0
        chapters = media.chapters()
        assert len(chapters) == 31
        for chapter, row in zip(chapters, rows):
            assert abs(float(chapter["start"] * chapter["time_base"]) - row["start_seconds"]) < .001
            assert abs(float(chapter["end"] * chapter["time_base"]) - row["end_seconds"]) < .001
        starts = {r["start_sample"]: i for i, r in enumerate(rows)}
        row_index = 0
        for frame in media.decode(video=0):
            sample = round(float(frame.pts * frame.time_base) * RATE)
            duration = round(float(frame.duration * frame.time_base) * RATE)
            assert sample > previous_sample and sample == previous_end
            assert duration > 0
            while row_index + 1 < len(rows) and sample >= rows[row_index]["end_sample"]:
                row_index += 1
            assert sample + duration <= rows[row_index]["end_sample"]
            all_frames += 1
            actual = frame.to_ndarray(format="rgb24")
            if sample in starts:
                i = starts[sample]
                assert i == row_index and frame.key_frame
                score = psnr(actual, expected_images[i])
                assert score > 34, (i + 1, score)
                prior_score = None
                if i:
                    assert previous_end == rows[i]["start_sample"]
                    prior_score = psnr(previous_image, expected_images[i - 1])
                    assert prior_score > 34
                transitions.append({"slide": i + 1, "start_sample": sample,
                                    "actual_seconds": sample / RATE, "key_frame": True,
                                    "first_frame_psnr_db": round(score, 2),
                                    "previous_last_frame_psnr_db": round(prior_score, 2) if prior_score else None})
                seen.add(i + 1)
                small = Image.fromarray(actual).resize((480, 270), Image.Resampling.LANCZOS)
                x, y = (i % 4) * 480, (i // 4) * 300
                contact.paste(small, (x, y))
                draw.text((x + 10, y + 274), f"Slide {i + 1:02} | {sample / RATE:.3f} s", fill="#333f4a")
            previous_sample, previous_end, previous_image, previous_row = sample, sample + duration, actual, row_index
        assert seen == set(range(1, 32)) and previous_end == timeline["duration_samples"]
    contact.save(WORK / "transition-contact-sheet.jpg", quality=90)
    # Compare decoded AAC against the PCM source near the beginning, middle and end.
    check_points = [rows[i]["start_seconds"] + 2 for i in (0, 15, 30)]
    audio_checks = []
    for point in check_points:
        target = round(point * 48000)
        with av.open(str(VIDEO)) as media:
            stream = media.streams.audio[0]
            media.seek(max(0, target - 48000), stream=stream, backward=True)
            chunks, first = [], None
            for frame in media.decode(audio=0):
                sample = round(float(frame.pts * frame.time_base) * 48000)
                if first is None:
                    first = sample
                chunks.append(frame.to_ndarray().reshape(-1))
                if sample + frame.samples >= target + 5 * 48000:
                    break
            raw = np.concatenate(chunks)
            offset = target - first
            assert offset >= 0
            decoded = resample_poly(raw[offset:offset + 5 * 48000], 1, 2)
        with sf.SoundFile(MASTER) as source:
            source.seek(round(point * RATE))
            expected = source.read(5 * RATE, dtype="float32")
        assert len(decoded) == len(expected)
        correlation = correlate(decoded, expected, method="fft")
        lags = correlation_lags(len(decoded), len(expected))
        delay = int(lags[np.argmax(correlation)])
        coefficient = float(np.corrcoef(decoded, expected)[0, 1])
        assert abs(delay) <= 1 and coefficient > .985, (point, delay, coefficient)
        audio_checks.append({"at_seconds": point, "delay_samples_at_24khz": delay, "correlation": round(coefficient, 6)})
    report = {
        "passed": True, "video": VIDEO.name, "duration_seconds": timeline["duration_seconds"],
        "narration_duration_seconds": timeline["narration_duration_seconds"],
        "size_bytes": VIDEO.stat().st_size, "video_sha256": sha(VIDEO),
        "dimensions": [WIDTH, HEIGHT], "video_codec": "h264", "pixel_format": "yuv420p",
        "audio_codec": "aac", "audio_channels": 1, "audio_sample_rate": 48000,
        "timeline_sample_rate": RATE, "chapter_count": 31, "faststart": True,
        "source_hashes_verified": True, "pcm_master_sample_exact": True,
        "all_silent_tails_verified": True, "all_frame_boundaries_contiguous": True,
        "no_early_slide_switches": True, "decoded_video_frames": all_frames,
        "slide_transition_checks": transitions, "audio_sync_checks": audio_checks,
        "full_subjective_listening_review_performed": False,
    }
    (OUT / "video-qa.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "file": str(VIDEO), "seconds": timeline["duration_seconds"],
                      "megabytes": VIDEO.stat().st_size / 1e6, "chapters": 31,
                      "minimum_transition_psnr": min(x["first_frame_psnr_db"] for x in transitions),
                      "audio_sync_checks": audio_checks}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    arguments = parser.parse_args()
    if arguments.validate_only:
        plan = json.loads((OUT / "timeline.json").read_text())
    else:
        plan = prepare()
        encode(plan)
    validate(plan)
