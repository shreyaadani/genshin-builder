# genshin-builder

An end-to-end computer vision pipeline that extracts structured artifact inventory data from iPad screen recordings of Genshin Impact — with zero manual data entry per artifact.

---

## The Problem

As a free-to-play player with a 300+ artifact inventory, manually reading every artifact to figure out optimal character builds is impractical. No public API exists for personal inventory data. All existing scanner tools are PC-oriented and incompatible with an iPad-first workflow.

**The goal:** Record your inventory once, run the pipeline, get a queryable artifact database.

---

## How It Works

```
iPad screen recording (.mp4)
         │
         ▼
Frame Extraction        — OpenCV pulls frames at 5fps
         │
         ▼
Stability Filter        — Removes blurry/transition frames via frame differencing
         │
         ▼
Deduplication           — Removes repeated frames of the same artifact
         │
         ▼
Region Cropping         — Crops each field from the right panel (set, slot, stats)
         │
         ▼
PaddleOCR               — Reads text from each cropped region
         │
         ▼
Schema Validation       — Validates against known Genshin data, flags mismatches
         │
         ▼
artifacts.json + artifacts.csv + flagged_review.json
```

---

## Recording Protocol

1. Open Artifact Inventory on iPad
2. Filter to 5-star artifacts (recommended)
3. Tap first artifact — right panel populates
4. Pause ~2 seconds
5. Tap next artifact
6. Repeat until all artifacts covered
7. Stop recording and transfer video to laptop

Human imprecision is handled automatically — the pipeline detects stable frames and removes duplicates regardless of tap timing.

---

## Output Schema

```json
{
  "id": "artifact_001",
  "set": "Golden Troupe",
  "slot": "Flower of Life",
  "rarity": 5,
  "level": 20,
  "main_stat": {
    "name": "HP",
    "value": 4780
  },
  "substats": [
    { "name": "DEF%", "value": 6.6 },
    { "name": "ATK", "value": 33 },
    { "name": "DEF", "value": 81 },
    { "name": "Energy Recharge%", "value": 10.4 }
  ],
  "equipped_character": "Furina",
  "extraction_confidence": "high",
  "flagged_for_review": false
}
```

---

## Stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| OpenCV | Video processing, frame extraction, frame differencing |
| PaddleOCR | Text extraction from cropped UI regions |
| Pure Python | Schema validation, confidence scoring, output writing |

Fully local. Fully free. No paid APIs. Runs on consumer hardware.

---

## Project Structure

```
genshin-builder/
│
├── main.py                  # Entry point — runs full pipeline
│
├── config/
│   ├── crop_regions.json    # Relative crop coordinates per field
│   └── genshin_schema.json  # Known sets, slots, stats for validation
│
├── pipeline/
│   ├── frame_extractor.py   # Video → raw frames
│   ├── stability_filter.py  # Remove blurry/transition frames
│   ├── deduplicator.py      # Remove duplicate artifact frames
│   ├── cropper.py           # Crop field regions from frame
│   ├── ocr_engine.py        # PaddleOCR wrapper
│   └── validator.py         # Schema validation + confidence scoring
│
├── output/
│   ├── writer.py            # JSON + CSV output
│   └── reviewer.py          # Flagged review file writer
│
└── data/                    # Generated files (gitignored)
    ├── artifacts.json
    ├── artifacts.csv
    └── flagged_review.json
```

---

## Setup

```bash
# Clone the repo
git clone https://github.com/your-username/genshin-builder.git
cd genshin-builder

# Create virtual environment with Python 3.11
py -3.11 -m venv genshin_env
genshin_env\Scripts\activate  # Windows
# source genshin_env/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

```bash
python main.py --video your_recording.mp4
```

Outputs will be written to the `data/` folder.

---

## Roadmap

| Phase | Description | Status |
|---|---|---|
| 1 | Video → Structured Artifact Database | 🚧 In Progress |
| 2 | Genshin Optimizer export format | Planned |
| 3 | Account planning (what to farm, what to level) | Planned |
| 4 | LLM reasoning layer ("best Furina build I can make?") | Planned |
| 5 | ML — artifact value prediction, keep/fodder classification | Planned |

---

## Why This Is Non-Trivial

- Input is noisy human-paced video, not clean controlled images
- Automated stability detection and deduplication handle variable tap timing
- Crop coordinates are resolution-independent (relative, not absolute pixels)
- Validation layer catches OCR errors using domain knowledge of valid Genshin values
- Works entirely offline with no external API dependencies

---

## Skills Demonstrated

`Computer Vision` `OCR` `ETL Pipeline Engineering` `Data Validation` `Python` `OpenCV` `PaddleOCR`