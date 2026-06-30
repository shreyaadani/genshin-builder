import re


# ── Known Genshin Data ────────────────────────────────────────────────────────

VALID_SLOTS = {
    "Flower of Life",
    "Plume of Death",
    "Sands of Eon",
    "Goblet of Eonothem",
    "Circlet of Logos",
}

VALID_MAIN_STATS = {
    "Flower of Life":    {"HP"},
    "Plume of Death":    {"ATK"},
    "Sands of Eon":      {"HP%", "DEF%", "ATK%", "Energy Recharge%", "Elemental Mastery"},
    "Goblet of Eonothem":{"HP%", "DEF%", "ATK%", "Elemental Mastery",
                          "Pyro DMG Bonus%", "Hydro DMG Bonus%", "Cryo DMG Bonus%",
                          "Electro DMG Bonus%", "Anemo DMG Bonus%", "Geo DMG Bonus%",
                          "Dendro DMG Bonus%", "Physical DMG Bonus%"},
    "Circlet of Logos":  {"HP%", "DEF%", "ATK%", "Elemental Mastery",
                          "CRIT Rate%", "CRIT DMG%", "Healing Bonus%"},
}

VALID_SUBSTATS = {
    "ATK", "ATK%", "DEF", "DEF%", "HP", "HP%",
    "Elemental Mastery", "Energy Recharge%", "CRIT Rate%", "CRIT DMG%",
}

# Position thresholds (y coordinate ranges from OCR output)
# Based on real iPad footage — these are the vertical zones for each field
# Tuned from actual OCR output positions
POSITION_MAP = {
    "set_name":          (150, 270),
    "slot":              (270, 380),
    "main_stat_name":    (380, 440),
    "main_stat_value":   (440, 620),
    "level":             (620, 720),
    "substat_1":         (720, 780),
    "substat_2":         (780, 840),
    "substat_3":         (840, 900),
    "substat_4":         (900, 960),
    "set_label":         (960, 1020),   # "Golden Troupe:" green text — we skip this
    "equipped_character":(1350, 1450),
}


# ── Text Cleanup ──────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Fix common OCR misreads before parsing.

    - Capital O → zero in numeric contexts
    - Common character substitutions
    """
    # Fix O → 0 in percentage/numeric values like "1O.4%" → "10.4%"
    text = re.sub(r'(?<=[0-9])O(?=[0-9.])', '0', text)
    text = re.sub(r'(?<=[0-9.])O(?=%)', '0', text)

    # Fix common OCR errors
    text = text.replace('$', 'S')
    text = text.strip()

    return text


# ── Field Mapping ─────────────────────────────────────────────────────────────

def map_blocks_to_fields(blocks: list[dict]) -> dict:
    """
    Map OCR text blocks to artifact fields using vertical position.

    Each field occupies a known vertical zone on the panel.
    We assign each text block to a field based on its y position.

    Args:
        blocks: List of {text, confidence, position} from ocr_engine

    Returns:
        Dict of {field_name: text_value} for each field found
    """
    fields = {}

    for block in blocks:
        pos = block["position"]
        text = clean_text(block["text"])
        conf = block["confidence"]

        # Skip very low confidence blocks — likely noise
        if conf < 0.3:
            continue

        # Find which field this position belongs to
        for field, (top, bottom) in POSITION_MAP.items():
            if top <= pos < bottom:
                if field == "set_label":
                    break  # Skip set bonus text
                fields[field] = {
                    "text": text,
                    "confidence": conf
                }
                break

    return fields


def parse_substat(text: str) -> dict | None:
    """
    Parse a substat string like "DEF+6.6%" or "ATK+33" into name and value.

    Args:
        text: Raw substat text from OCR

    Returns:
        {"name": "DEF%", "value": 6.6} or None if unparseable
    """
    # Match patterns like: DEF+6.6% or ATK+33 or HP+215
    match = re.match(r'^(.+?)\+([0-9,.]+)(%?)$', text.strip())
    if not match:
        return None

    stat_name = match.group(1).strip()
    value_str = match.group(2).replace(',', '')
    is_percent = match.group(3) == '%'

    try:
        value = float(value_str)
    except ValueError:
        return None

    # Add % to stat name if it's a percentage stat
    if is_percent:
        stat_name = stat_name + "%"

    return {"name": stat_name, "value": value}


def parse_level(text: str) -> int | None:
    """
    Parse level badge like "+20" or "+13" into an integer.

    Args:
        text: Raw level text from OCR

    Returns:
        Integer level or None if unparseable
    """
    match = re.match(r'^\+?(\d+)$', text.strip())
    if match:
        return int(match.group(1))
    return None


def parse_main_stat_value(text: str) -> float | None:
    """
    Parse main stat value like "4,780" or "118" into a number.

    Args:
        text: Raw main stat value text from OCR

    Returns:
        Float value or None if unparseable
    """
    cleaned = text.replace(',', '').replace('%', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_equipped(text: str) -> str | None:
    """
    Parse equipped character text like "Equipped: Furina" into just "Furina".

    Args:
        text: Raw equipped text from OCR

    Returns:
        Character name string or None
    """
    if "Equipped:" in text:
        return text.replace("Equipped:", "").strip()
    if "Equipped" in text:
        return text.replace("Equipped", "").strip(" :")
    return None


# ── Validation ────────────────────────────────────────────────────────────────

def validate_artifact(fields: dict) -> dict:
    """
    Parse and validate all artifact fields.
    Returns a structured artifact object with confidence scoring.

    Args:
        fields: Dict of {field_name: {text, confidence}} from map_blocks_to_fields

    Returns:
        Dict with parsed artifact data, confidence, and flags
    """
    artifact = {
        "set": None,
        "slot": None,
        "main_stat": {"name": None, "value": None},
        "level": None,
        "substats": [],
        "equipped_character": None,
        "extraction_confidence": "high",
        "flagged_for_review": False,
        "flags": []
    }

    flags = []

    # ── Set name ──
    if "set_name" in fields:
        artifact["set"] = fields["set_name"]["text"]
    else:
        flags.append("missing_set_name")

    # ── Slot ──
    if "slot" in fields:
        slot_text = fields["slot"]["text"]
        if slot_text in VALID_SLOTS:
            artifact["slot"] = slot_text
        else:
            artifact["slot"] = slot_text
            flags.append(f"invalid_slot: {slot_text}")
    else:
        flags.append("missing_slot")

    # ── Main stat name ──
    if "main_stat_name" in fields:
        artifact["main_stat"]["name"] = fields["main_stat_name"]["text"]
    else:
        flags.append("missing_main_stat_name")

    # ── Main stat value ──
    if "main_stat_value" in fields:
        value = parse_main_stat_value(fields["main_stat_value"]["text"])
        if value is not None:
            artifact["main_stat"]["value"] = value
        else:
            flags.append(f"unparseable_main_stat_value: {fields['main_stat_value']['text']}")
    else:
        flags.append("missing_main_stat_value")

  # ── Validate main stat against slot ──
    if artifact["slot"] and artifact["main_stat"]["name"]:
        slot = artifact["slot"]
        main = artifact["main_stat"]["name"]
        if slot in VALID_MAIN_STATS:
            if main not in VALID_MAIN_STATS[slot]:
                # Try adding % — OCR sometimes drops it
                if main + "%" in VALID_MAIN_STATS[slot]:
                    artifact["main_stat"]["name"] = main + "%"
                else:
                    flags.append(f"invalid_main_stat_for_slot: {main} on {slot}")

    # ── Level ──
    if "level" in fields:
        level = parse_level(fields["level"]["text"])
        if level is not None and 0 <= level <= 20:
            artifact["level"] = level
        else:
            flags.append(f"invalid_level: {fields['level']['text']}")
    else:
        flags.append("missing_level")

    # ── Substats ──
    for i in range(1, 5):
        key = f"substat_{i}"
        if key in fields:
            parsed = parse_substat(fields[key]["text"])
            if parsed:
                artifact["substats"].append(parsed)
            else:
                flags.append(f"unparseable_substat_{i}: {fields[key]['text']}")

    # ── Equipped character ──
    if "equipped_character" in fields:
        character = parse_equipped(fields["equipped_character"]["text"])
        artifact["equipped_character"] = character

    # ── Confidence scoring ──
    critical_flags = [f for f in flags if "missing" in f or "invalid" in f]

    if len(critical_flags) == 0:
        artifact["extraction_confidence"] = "high"
    elif len(critical_flags) == 1:
        artifact["extraction_confidence"] = "medium"
    else:
        artifact["extraction_confidence"] = "low"
        artifact["flagged_for_review"] = True

    artifact["flags"] = flags

    return artifact


def process_ocr_output(blocks: list[dict]) -> dict:
    """
    Full pipeline from raw OCR blocks to validated artifact.
    Single entry point used by main.py.

    Args:
        blocks: Raw OCR output from ocr_engine.read_panel()

    Returns:
        Validated artifact dict
    """
    fields = map_blocks_to_fields(blocks)
    artifact = validate_artifact(fields)
    return artifact


# ── Test ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import glob
    import os
    import sys
    import cv2
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from pipeline.cropper import crop_panel
    from pipeline.ocr_engine import read_panel

    unique_dir = "data/unique_frames"
    frame_paths = sorted(glob.glob(os.path.join(unique_dir, "*.jpg")))

    if not frame_paths:
        print("No unique frames found. Run deduplicator.py first.")
    else:
        for i, path in enumerate(frame_paths[:5]):
            print(f"\n{'='*60}")
            print(f"Frame: {path}")

            frame = cv2.imread(path)
            if frame is None:
                continue

            panel = crop_panel(frame)
            blocks = read_panel(panel)
            artifact = process_ocr_output(blocks)

            print(f"  Set:      {artifact['set']}")
            print(f"  Slot:     {artifact['slot']}")
            print(f"  Main:     {artifact['main_stat']}")
            print(f"  Level:    {artifact['level']}")
            print(f"  Substats: {artifact['substats']}")
            print(f"  Equipped: {artifact['equipped_character']}")
            print(f"  Confidence: {artifact['extraction_confidence']}")
            if artifact['flags']:
                print(f"  Flags:    {artifact['flags']}")