import cv2
import numpy as np
import os


def is_stable(frame1: np.ndarray, frame2: np.ndarray, threshold: float = 5.0) -> bool:
    """
    Compare two frames to determine if the screen is stable (not animating/scrolling).

    Args:
        frame1: First frame as numpy array
        frame2: Second frame as numpy array
        threshold: Mean pixel difference below this = stable (default 5.0)

    Returns:
        True if frames are stable (similar), False if transitioning
    """
    # Convert both frames to grayscale — we only care about brightness changes
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    # Calculate absolute difference between frames
    diff = cv2.absdiff(gray1, gray2)

    # Mean difference across all pixels
    mean_diff = np.mean(diff)

    return mean_diff < threshold


def filter_stable_frames(frame_paths: list[str], threshold: float = 5.0) -> list[str]:
    """
    Filter a list of frame paths, keeping only stable frames.

    A frame is stable if it is sufficiently similar to the next frame —
    meaning the screen is not moving or transitioning.

    Args:
        frame_paths: List of paths to extracted frames (in order)
        threshold: Pixel difference threshold for stability (default 5.0)

    Returns:
        List of paths to stable frames only
    """

    if len(frame_paths) < 2:
        return frame_paths

    print(f"Stability filtering {len(frame_paths)} frames...")

    stable_paths = []
    skipped = 0

    for i in range(len(frame_paths) - 1):
        frame1 = cv2.imread(frame_paths[i])
        frame2 = cv2.imread(frame_paths[i + 1])

        if frame1 is None or frame2 is None:
            print(f"  Warning: Could not read frame at index {i}, skipping")
            skipped += 1
            continue

        if is_stable(frame1, frame2, threshold):
            stable_paths.append(frame_paths[i])
        else:
            skipped += 1

    print(f"Stability filter complete:")
    print(f"  Stable frames kept: {len(stable_paths)}")
    print(f"  Unstable frames removed: {skipped}")

    return stable_paths


if __name__ == "__main__":
    """
    Quick test — point at a folder of extracted frames.
    Usage: python stability_filter.py
    """
    import glob

    frame_dir = "data/raw_frames"
    frame_paths = sorted(glob.glob(os.path.join(frame_dir, "*.jpg")))

    if not frame_paths:
        print(f"No frames found in {frame_dir}")
        print("Run frame_extractor.py first to generate frames")
    else:
        stable = filter_stable_frames(frame_paths)
        print(f"\nFirst 5 stable frame paths:")
        for p in stable[:5]:
            print(f"  {p}")

    """
    What it does:

    Takes consecutive frames and compares them pixel by pixel
    If the mean difference is below the threshold (5.0) → screen is stable → keep the frame
    If difference is high → screen is mid-transition/scroll → discard
    The threshold=5.0 is a starting value we may need to tune once we test on real footage

    The key idea: A blurry transition frame will look very different from the next frame.
    A stable artifact panel will look almost identical to the next frame. That difference is what we measure.
    
    """        