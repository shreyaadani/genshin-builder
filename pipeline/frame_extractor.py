import cv2
import os


def extract_frames(video_path: str, output_dir: str, fps: int = 5) -> list[str]:
    """
    Extract frames from a video file at a given fps rate.

    Args:
        video_path: Path to the input video file (.mp4 or .mov)
        output_dir: Directory to save extracted frames
        fps: How many frames to extract per second of video (default 5)

    Returns:
        List of file paths to the extracted frames
    """

    # Validate video file exists
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    # Get video properties
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_seconds = total_frames / video_fps

    print(f"Video info:")
    print(f"  FPS: {video_fps:.2f}")
    print(f"  Total frames: {total_frames}")
    print(f"  Duration: {duration_seconds:.1f} seconds")
    print(f"  Extracting at: {fps} fps")

    # Calculate frame interval — how many raw frames to skip between extractions
    frame_interval = int(video_fps / fps)
    if frame_interval < 1:
        frame_interval = 1

    extracted_paths = []
    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Save frame if it falls on our interval
        if frame_count % frame_interval == 0:
            frame_filename = f"frame_{saved_count:05d}.jpg"
            frame_path = os.path.join(output_dir, frame_filename)
            cv2.imwrite(frame_path, frame)
            extracted_paths.append(frame_path)
            saved_count += 1

        frame_count += 1

    cap.release()

    print(f"\nExtraction complete:")
    print(f"  Frames extracted: {saved_count}")
    print(f"  Saved to: {output_dir}")

    return extracted_paths


if __name__ == "__main__":
    # Quick test — replace with your actual video path
    import sys

    if len(sys.argv) < 2:
        print("Usage: python frame_extractor.py <video_path>")
        print("Example: python frame_extractor.py recording.mp4")
        sys.exit(1)

    video_path = sys.argv[1]
    output_dir = "data/raw_frames"

    frames = extract_frames(video_path, output_dir, fps=5)
    print(f"\nFirst 5 frame paths:")
    for p in frames[:5]:
        print(f"  {p}")


        """
        What it does:

        Opens the video with OpenCV
        Reads video FPS and duration
        Extracts frames at 5fps (so every 0.2 seconds of video = one frame)
        Saves them as numbered JPGs to data/raw_frames/
        Returns a list of file paths for the next stage
        """      