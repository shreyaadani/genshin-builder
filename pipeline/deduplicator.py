import cv2
import numpy as np
import os


# The right panel starts at roughly 65% of the screen width
# We only compare this region for deduplication — not the full frame
# This avoids false positives from the grid side changing while panel stays same
RIGHT_PANEL_START_RATIO = 0.65


def get_right_panel(frame: np.ndarray) -> np.ndarray:
    """
    Crop just the right panel from a full inventory screen frame.

    Args:
        frame: Full frame as numpy array

    Returns:
        Cropped right panel as numpy array
    """
    h, w = frame.shape[:2]
    panel_start_x = int(w * RIGHT_PANEL_START_RATIO)
    return frame[:, panel_start_x:]


def hash_frame(frame: np.ndarray, size: int = 16) -> np.ndarray:
    """
    Generate a perceptual hash of a frame for fast comparison.

    Resize to a tiny fixed size and convert to grayscale —
    gives us a compact fingerprint for similarity comparison.

    Args:
        frame: Frame as numpy array
        size: Hash resolution (default 16x16)

    Returns:
        Flattened grayscale pixel array as the hash
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (size, size))
    return resized.flatten().astype(np.float32)


def frames_are_duplicate(hash1: np.ndarray, hash2: np.ndarray, threshold: float = 10.0) -> bool:
    """
    Compare two frame hashes to determine if they show the same artifact.

    Args:
        hash1: Hash of first frame
        hash2: Hash of second frame
        threshold: Mean difference below this = duplicate (default 10.0)

    Returns:
        True if frames are duplicates of the same artifact
    """
    diff = np.mean(np.abs(hash1 - hash2))
    return diff < threshold


def deduplicate_frames(frame_paths: list[str], threshold: float = 10.0) -> list[str]:
    """
    Remove duplicate frames showing the same artifact.

    Compares the right panel region of each frame against the last
    kept frame. If they look the same, discard as duplicate.

    Args:
        frame_paths: List of stable frame paths (output of stability_filter)
        threshold: Similarity threshold for duplicate detection (default 10.0)

    Returns:
        List of unique frame paths — one per artifact
    """

    if not frame_paths:
        return []

    print(f"Deduplicating {len(frame_paths)} stable frames...")

    unique_paths = []
    last_hash = None
    duplicates_removed = 0

    for path in frame_paths:
        frame = cv2.imread(path)
        if frame is None:
            print(f"  Warning: Could not read {path}, skipping")
            continue

        # Only compare the right panel region
        panel = get_right_panel(frame)
        current_hash = hash_frame(panel)

        if last_hash is None:
            # First frame always kept
            unique_paths.append(path)
            last_hash = current_hash
            continue

        if frames_are_duplicate(current_hash, last_hash, threshold):
            duplicates_removed += 1
        else:
            # New artifact detected
            unique_paths.append(path)
            last_hash = current_hash

    print(f"Deduplication complete:")
    print(f"  Unique artifacts found: {len(unique_paths)}")
    print(f"  Duplicate frames removed: {duplicates_removed}")

    return unique_paths


def save_unique_frames(unique_paths: list[str], output_dir: str) -> None:
    """
    Copy unique frames to a separate folder for visual verification.
    Used during testing only — not needed in the full pipeline.

    Args:
        unique_paths: List of unique frame paths
        output_dir: Directory to copy unique frames into
    """
    import shutil
    os.makedirs(output_dir, exist_ok=True)

    for i, path in enumerate(unique_paths):
        filename = f"unique_{i:05d}.jpg"
        dest = os.path.join(output_dir, filename)
        shutil.copy2(path, dest)

    print(f"\nUnique frames saved to: {output_dir}")
    print(f"  Open this folder to visually verify each artifact is different")


if __name__ == "__main__":
    """
    Quick test — point at a folder of extracted frames.
    Usage: python pipeline/deduplicator.py
    """
    import glob
    import sys

    frame_dir = "data/raw_frames"
    unique_dir = "data/unique_frames"

    frame_paths = sorted(glob.glob(os.path.join(frame_dir, "*.jpg")))

    if not frame_paths:
        print(f"No frames found in {frame_dir}")
        print("Run frame_extractor.py first to generate frames")
        sys.exit(1)

    # Run stability filter then deduplication
    from stability_filter import filter_stable_frames
    stable = filter_stable_frames(frame_paths)
    unique = deduplicate_frames(stable,threshold=3.0)

    # Save unique frames for visual verification
    save_unique_frames(unique, unique_dir)