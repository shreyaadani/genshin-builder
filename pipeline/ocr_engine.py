import easyocr
import numpy as np
import cv2


# Initialize EasyOCR once at module level
# gpu=False — use CPU, works on any hardware including Intel Arc
# lang_list=['en'] — English only
reader = easyocr.Reader(['en'], gpu=False)


def read_panel(panel: np.ndarray) -> list[dict]:
    """
    Run OCR on a cropped artifact panel image.

    Returns a list of detected text blocks, each with:
    - text: the string that was read
    - confidence: how confident EasyOCR is (0.0 to 1.0)
    - position: top-y coordinate for vertical ordering
                used to map text to fields by position

    Args:
        panel: Cropped right panel image (numpy array, BGR)

    Returns:
        List of dicts sorted top to bottom by vertical position
    """

    # EasyOCR accepts BGR directly — no conversion needed
    results = reader.readtext(panel)

    # Each result is: (bbox, text, confidence)
    # bbox is [[x1,y1],[x2,y1],[x2,y2],[x1,y2]] — 4 corners

    if not results:
        return []

    blocks = []

    for (bbox, text, confidence) in results:
        if not text.strip():
            continue

        # Top-left y coordinate for vertical ordering
        top_y = bbox[0][1]

        blocks.append({
            "text": text.strip(),
            "confidence": round(float(confidence), 4),
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

            '''
            What ocr_engine.py does:
            reader — initialized once at the top

            Loads EasyOCR's models once when the module is imported. gpu=False means it runs on CPU — works on any hardware, no CUDA or Intel Arc issues. We only load English since Genshin's UI is English.

            read_panel()

            Takes the cropped panel image
            Calls reader.readtext(panel) — one clean call that runs the full OCR
            EasyOCR returns a list of tuples: (bounding_box, text, confidence)
            The bounding box has 4 corners — we take the top-left y coordinate to know where vertically on the panel this text lives
            For each text block records: the text, confidence score, and vertical position
            Sorts everything top to bottom by vertical position
            Why vertical position matters:

            Genshin's panel is always the same order top to bottom — set name, slot, main stat, level, substats, equipped character. Position tells us what field each text belongs to without any hardcoding.

            print_blocks()

            Debug helper only — prints a clean table of everything OCR found. Not used in the real pipeline.
                        '''