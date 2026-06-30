import argparse
import os
import sys
import time
import glob
import cv2

from pipeline.frame_extractor import extract_frames
from pipeline.stability_filter import filter_stable_frames
from pipeline.deduplicator import deduplicate_frames
from pipeline.cropper import crop_panel
from pipeline.ocr_engine import read_panel
from pipeline.validator import process_ocr_output
from output.writer import write_all


def run_pipeline(video_path: str, output_dir: str = "data") -> None:
    """
    Run the full Genshin artifact extraction pipeline.

    Steps:
    1. Extract frames from video
    2. Filter to stable frames only
    3. Deduplicate — one frame per artifact
    4. Crop right panel from each frame
    5. Run OCR on each panel
    6. Validate and parse OCR output
    7. Write artifacts.json, artifacts.csv, flagged_review.json, run_log.txt

    Args:
        video_path: Path to the iPad screen recording
        output_dir: Where to write output files (default: data/)
    """

    start_time = time.time()

    print("\n" + "=" * 60)
    print("  Genshin Builder — Artifact Extraction Pipeline")
    print("=" * 60)

    # ── Step 1: Frame Extraction ──────────────────────────────────
    print("\n[1/6] Extracting frames from video...")
    frames_dir = os.path.join(output_dir, "raw_frames")
    frame_paths = extract_frames(video_path, frames_dir, fps=5)
    print(f"      {len(frame_paths)} frames extracted")

    if not frame_paths:
        print("ERROR: No frames extracted. Check your video file.")
        sys.exit(1)

    # ── Step 2: Stability Filter ──────────────────────────────────
    print("\n[2/6] Filtering stable frames...")
    stable_paths = filter_stable_frames(frame_paths)
    print(f"      {len(stable_paths)} stable frames kept")

    if not stable_paths:
        print("ERROR: No stable frames found. Try recording at a slower pace.")
        sys.exit(1)

    # ── Step 3: Deduplication ─────────────────────────────────────
    print("\n[3/6] Removing duplicate artifact frames...")
    unique_paths = deduplicate_frames(stable_paths, threshold=3.0)
    print(f"      {len(unique_paths)} unique artifacts found")

    if not unique_paths:
        print("ERROR: No unique frames found after deduplication.")
        sys.exit(1)

    # ── Steps 4-6: Crop → OCR → Validate ─────────────────────────
    print(f"\n[4-6/6] Cropping, reading, and validating {len(unique_paths)} artifacts...")
    print("        This may take a few minutes on CPU...\n")

    artifacts = []
    high = medium = low = 0

    for i, path in enumerate(unique_paths):
        frame = cv2.imread(path)
        if frame is None:
            print(f"  Warning: Could not read {path}, skipping")
            continue

        # Crop panel
        panel = crop_panel(frame)

        # OCR
        blocks = read_panel(panel)

        # Validate and parse
        artifact = process_ocr_output(blocks)

        # Add ID
        artifact["id"] = f"artifact_{i+1:03d}"

        # Track confidence
        conf = artifact["extraction_confidence"]
        if conf == "high":
            high += 1
        elif conf == "medium":
            medium += 1
        else:
            low += 1

        artifacts.append(artifact)

        # Progress indicator
        print(f"  [{i+1:3d}/{len(unique_paths)}] {conf:6s} — {artifact.get('set', 'unknown')} / {artifact.get('slot', 'unknown')}")

    # ── Step 7: Write Output ──────────────────────────────────────
    elapsed = time.time() - start_time
    elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

    print(f"\n[7/7] Writing output files...")

    stats = {
        "video_path":       video_path,
        "raw_frames":       len(frame_paths),
        "stable_frames":    len(stable_paths),
        "unique_frames":    len(unique_paths),
        "parsed":           len(artifacts),
        "high_confidence":  high,
        "medium_confidence":medium,
        "low_confidence":   low,
        "flagged":          sum(1 for a in artifacts if a.get("flagged_for_review")),
        "processing_time":  elapsed_str,
    }

    write_all(artifacts, stats, output_dir)

    # ── Summary ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Pipeline Complete")
    print("=" * 60)
    print(f"  Total artifacts processed : {len(artifacts)}")
    print(f"  High confidence           : {high}")
    print(f"  Medium confidence         : {medium}")
    print(f"  Low confidence (skipped)  : {low}")
    print(f"  Processing time           : {elapsed_str}")
    print(f"  Output directory          : {output_dir}/")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genshin Builder — Extract artifact inventory from iPad screen recording"
    )
    parser.add_argument(
        "--video",
        required=True,
        help="Path to your iPad screen recording (e.g. data/recording.mp4)"
    )
    parser.add_argument(
        "--output",
        default="data",
        help="Output directory for artifacts.json, artifacts.csv etc. (default: data/)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"ERROR: Video file not found: {args.video}")
        sys.exit(1)

    run_pipeline(args.video, args.output)