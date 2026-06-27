import cv2
import numpy as np
import os


def detect_right_panel(frame: np.ndarray) -> tuple[int, int, int, int]:
    """
    Auto-detect the right panel boundary in an inventory screen frame.

    The right panel has a distinct light/cream background compared to
    the dark artifact grid on the left. We find where that light region
    starts horizontally and use the full frame height vertically.

    Args:
        frame: Full frame as numpy array (BGR)

    Returns:
        (x1, y1, x2, y2) pixel coordinates of the right panel
    """
    h, w = frame.shape[:2]

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Look at a horizontal slice through the middle of the frame
    mid_row = gray[h // 2, :]

    # Smooth to avoid noise
    smoothed = np.convolve(mid_row.astype(float), np.ones(20)/20, mode='same')

    # Search only in right 45% of screen — that's where panel lives
    search_start = int(w * 0.64)
    search_zone = smoothed[search_start:]

    # Find first significant brightness jump = panel boundary
    threshold = 30
    panel_start_x = search_start  # fallback

    for i in range(1, len(search_zone)):
        if search_zone[i] - search_zone[i-1] > threshold:
            panel_start_x = search_start + i
            break

    return (panel_start_x, 0, w, h)


def crop_panel(frame: np.ndarray) -> np.ndarray:
    """
    Crop just the right panel from a full inventory screen frame.

    Args:
        frame: Full inventory screen frame

    Returns:
        Cropped right panel as numpy array, ready for OCR
    """
    x1, y1, x2, y2 = detect_right_panel(frame)
    panel = frame[y1:y2, x1:x2]
    return panel


if __name__ == "__main__":
    """
    Test cropper on unique frames.
    Saves cropped panels to data/crop_verification/ for visual check.
    Usage: python pipeline/cropper.py
    """
    import glob

    unique_dir = "data/unique_frames"
    crops_dir = "data/crop_verification"

    frame_paths = sorted(glob.glob(os.path.join(unique_dir, "*.jpg")))

    if not frame_paths:
        print(f"No unique frames found in {unique_dir}")
        print("Run deduplicator.py first")
    else:
        os.makedirs(crops_dir, exist_ok=True)

        # Test on first 3 unique frames
        for i, path in enumerate(frame_paths[:3]):
            print(f"\nProcessing: {path}")
            frame = cv2.imread(path)

            if frame is None:
                print(f"  Could not read frame")
                continue

            panel = crop_panel(frame)
            out_path = os.path.join(crops_dir, f"panel_{i:03d}.jpg")
            cv2.imwrite(out_path, panel)
            print(f"  Panel cropped: {panel.shape[1]}x{panel.shape[0]} px")
            print(f"  Saved to: {out_path}")

        print(f"\nOpen {crops_dir} to verify panels look correct")