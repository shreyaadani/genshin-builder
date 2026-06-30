import json
import csv
import os
from datetime import datetime


def write_json(artifacts: list[dict], output_path: str) -> None:
    """
    Write full artifact database to JSON.

    Args:
        artifacts: List of validated artifact dicts
        output_path: Where to save artifacts.json
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    output = {
        "generated_at": datetime.now().isoformat(),
        "total_artifacts": len(artifacts),
        "artifacts": artifacts
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"JSON written: {output_path} ({len(artifacts)} artifacts)")


def write_csv(artifacts: list[dict], output_path: str) -> None:
    """
    Write flat artifact database to CSV.
    One row per artifact, substats flattened into separate columns.

    Args:
        artifacts: List of validated artifact dicts
        output_path: Where to save artifacts.csv
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # CSV columns
    fieldnames = [
        "id",
        "set",
        "slot",
        "level",
        "main_stat_name",
        "main_stat_value",
        "substat_1_name", "substat_1_value",
        "substat_2_name", "substat_2_value",
        "substat_3_name", "substat_3_value",
        "substat_4_name", "substat_4_value",
        "equipped_character",
        "extraction_confidence",
        "flagged_for_review",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for artifact in artifacts:
            row = {
                "id":                   artifact.get("id", ""),
                "set":                  artifact.get("set", ""),
                "slot":                 artifact.get("slot", ""),
                "level":                artifact.get("level", ""),
                "main_stat_name":       artifact.get("main_stat", {}).get("name", ""),
                "main_stat_value":      artifact.get("main_stat", {}).get("value", ""),
                "equipped_character":   artifact.get("equipped_character", ""),
                "extraction_confidence":artifact.get("extraction_confidence", ""),
                "flagged_for_review":   artifact.get("flagged_for_review", False),
            }

            # Flatten substats
            substats = artifact.get("substats", [])
            for i in range(4):
                if i < len(substats):
                    row[f"substat_{i+1}_name"]  = substats[i].get("name", "")
                    row[f"substat_{i+1}_value"] = substats[i].get("value", "")
                else:
                    row[f"substat_{i+1}_name"]  = ""
                    row[f"substat_{i+1}_value"] = ""

            writer.writerow(row)

    print(f"CSV written: {output_path} ({len(artifacts)} artifacts)")


def write_flagged(artifacts: list[dict], output_path: str) -> None:
    """
    Write flagged artifacts to a separate JSON for manual review.
    Only includes artifacts with flagged_for_review=True.

    Args:
        artifacts: Full list of validated artifact dicts
        output_path: Where to save flagged_review.json
    """
    flagged = [a for a in artifacts if a.get("flagged_for_review", False)]

    if not flagged:
        print("No flagged artifacts — skipping flagged_review.json")
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(flagged, f, indent=2, ensure_ascii=False)

    print(f"Flagged review written: {output_path} ({len(flagged)} artifacts)")


def write_log(stats: dict, output_path: str) -> None:
    """
    Write a plain text run log with pipeline stats.

    Args:
        stats: Dict of pipeline statistics
        output_path: Where to save run_log.txt
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("Genshin Builder — Pipeline Run Log\n")
        f.write("=" * 40 + "\n")
        f.write(f"Run at:              {datetime.now().isoformat()}\n")
        f.write(f"Video file:          {stats.get('video_path', 'unknown')}\n")
        f.write(f"Raw frames:          {stats.get('raw_frames', 0)}\n")
        f.write(f"Stable frames:       {stats.get('stable_frames', 0)}\n")
        f.write(f"Unique artifacts:    {stats.get('unique_frames', 0)}\n")
        f.write(f"Successfully parsed: {stats.get('parsed', 0)}\n")
        f.write(f"High confidence:     {stats.get('high_confidence', 0)}\n")
        f.write(f"Medium confidence:   {stats.get('medium_confidence', 0)}\n")
        f.write(f"Low confidence:      {stats.get('low_confidence', 0)}\n")
        f.write(f"Flagged for review:  {stats.get('flagged', 0)}\n")
        f.write(f"Processing time:     {stats.get('processing_time', 'unknown')}\n")

    print(f"Log written: {output_path}")


def write_all(artifacts: list[dict], stats: dict, output_dir: str = "data") -> None:
    """
    Write all output files in one call.
    This is the main entry point used by main.py.

    Args:
        artifacts: List of validated artifact dicts
        stats: Pipeline run statistics
        output_dir: Base directory for output files
    """
    # Only write high and medium confidence artifacts to main output
    clean = [a for a in artifacts if a.get("extraction_confidence") != "low"]

    write_json(clean,    os.path.join(output_dir, "artifacts.json"))
    write_csv(clean,     os.path.join(output_dir, "artifacts.csv"))
    write_flagged(clean, os.path.join(output_dir, "flagged_review.json"))
    write_log(stats,     os.path.join(output_dir, "run_log.txt"))

    print(f"\nDone. {len(clean)} artifacts written to {output_dir}/")