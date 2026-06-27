from paddleocr import PaddleOCR
import numpy as np
import cv2


# Initialize PaddleOCR once at module level
# use_textline_orientation=False — Genshin UI text is always upright
# use_doc_orientation_classify=False — no need to detect document rotation
# use_doc_unwarping=False — no need to unwarp, screenshots are flat
# lang='en' — English text only
_ocr = PaddleOCR(
    use_textline_orientation=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    lang='en'
)


def read_panel(panel: np.ndarray) -> list[dict]:
    """
    Run OCR on a cropped artifact panel image.

    Returns a list of detected text blocks, each with:
    - text: the string that was read
    - confidence: how confident PaddleOCR is (0.0 to 1.0)
    - position: top-y coordinate of the text on the panel
                used later to map text to fields by vertical position

    Args:
        panel: Cropped right panel image (numpy array, BGR)

    Returns:
        List of dicts sorted top to bottom by vertical position
    """

    # PaddleOCR expects RGB, OpenCV gives BGR
    panel_rgb = cv2.cvtColor(panel, cv2.COLOR_BGR2RGB)

    # Run OCR — returns list of OCRResult objects
    results = _ocr.predict(panel_rgb)

    if not results:
        return []

    result = results[0]  # One result per image

    # Extract fields from result object
    rec_texts  = result["rec_texts"]   # List of text strings
    rec_scores = result["rec_scores"]  # List of confidence scores
    rec_polys  = result["rec_polys"]   # List of bounding boxes (4 corner points each)

    if not rec_texts:
        return []

    blocks = []

    for text, score, poly in zip(rec_texts, rec_scores, rec_polys):
        if not text.strip():
            continue

        # Top-left y coordinate for vertical ordering
        top_y = poly[0][1]

        blocks.append({
            "text": text.strip(),
            "confidence": round(float(score), 4),
            "position": round(float(top_y), 1),
        })

    # Sort top to bottom
    blocks.sort(key=lambda b: b["position"])

    return blocks


def print_blocks(blocks: list[dict]):
    """
    Pretty print OCR results for debugging.

    Args:
        blocks: List of text blocks from read_panel()
    """
    print(f"\nOCR Results ({len(blocks)} blocks detected):")
    print(f"{'Position':>10}  {'Confidence':>10}  Text")
    print("-" * 60)
    for b in blocks:
        print(f"{b['position']:>10.1f}  {b['confidence']:>10.4f}  {b['text']}")


if __name__ == "__main__":
    """
    Test OCR on unique frames.
    Usage: python pipeline/ocr_engine.py
    """
    import glob
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from pipeline.cropper import crop_panel

    unique_dir = "data/unique_frames"
    frame_paths = sorted(glob.glob(os.path.join(unique_dir, "*.jpg")))

    if not frame_paths:
        print(f"No unique frames found in {unique_dir}")
        print("Run deduplicator.py first")
    else:
        # Test on first 3 frames
        for i, path in enumerate(frame_paths[:3]):
            print(f"\n{'='*60}")
            print(f"Frame: {path}")

            frame = cv2.imread(path)
            if frame is None:
                print("Could not read frame")
                continue

            panel = crop_panel(frame)
            blocks = read_panel(panel)
            print_blocks(blocks)