import argparse
from pathlib import Path


STATE_DIR = Path(__file__).parent / "states"

# Position in the custom address order -> phone number. Positions become
# three-digit ranks in steps of 10: 010, 020, 030, etc. This leaves room to
# insert future files between existing ranks.
# Position 2 / rank 030 (Цветочная) is intentionally absent because there is no
# state file for that address in the current output.
PHONE_POSITIONS = {
    0: "79043989045",   # Академика Чазова, 1, кв. 163
    1: "79527603115",   # Академика Чазова, 2, кв. 115
    3: "79081538274",   # Героев Донбасса, 10, кв. 274
    4: "79535578193",   # Героев Донбасса, 11, кв. 249
    5: "79043989067",   # Героев Донбасса, 12, кв. 121
    6: "79050116600",   # Героев Донбасса, 12, кв. 215
    7: "79503411564",   # Героев Донбасса, 15, кв. 64
    8: "79082317842",   # Героев Донбасса, 7, кв. 81
    9: "79040518114",   # Максима Горького, 23А, кв. 1811
    10: "79519037443",  # Максима Горького, 23А, кв. 523
    11: "79043960929",  # Максима Горького, 23А, кв. 609
    12: "79081546374",  # Максима Горького, 23А, кв. 724
    13: "79033674961",  # Маршала Баграмяна, 2, кв. 19
    14: "79878615969",  # Новокузнечихинская, 1, кв. 122
    15: "79524463813",  # Новокузнечихинская, 13, кв. 13
    16: "79043988632",  # Новокузнечихинская, 14, кв. 240
    17: "79081546191",  # Новокузнечихинская, 2, кв. 190
    18: "79026842701",  # Новокузнечихинская, 8, кв. 201
    19: "79026829556",  # Родионова, 31, кв. 245
    20: "79081615834",  # Родионова, 31, кв. 77
    21: "79081548685",  # Тимирязева, 7, к. 5, кв. 7
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Rename state files according to the custom address order."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned renames without changing any files.",
    )
    return parser.parse_args()


def find_state_files(phone):
    candidates = [STATE_DIR / f"{phone}.json"]
    candidates.extend(STATE_DIR.glob(f"*-{phone}.json"))
    return sorted({path for path in candidates if path.exists()})


def get_rank(position):
    return (position + 1) * 10


def main():
    args = parse_args()
    missing = []
    duplicates = []
    rename_plan = []

    # Build and validate the complete plan before changing any filename.
    for position, phone in PHONE_POSITIONS.items():
        destination = STATE_DIR / f"{get_rank(position):03d}-{phone}.json"
        matches = find_state_files(phone)

        if not matches:
            missing.append(f"{phone}.json")
        elif len(matches) > 1:
            duplicates.append((phone, matches))
        elif matches[0] != destination:
            rename_plan.append((matches[0], destination))

    if missing or duplicates:
        print("Nothing was renamed.")

    if missing:
        print("Missing state files:")
        for filename in missing:
            print(f"- {filename}")

    if duplicates:
        print("Multiple state files found for the same phone:")
        for phone, matches in duplicates:
            filenames = ", ".join(path.name for path in matches)
            print(f"- {phone}: {filenames}")

    if missing or duplicates:
        return 1

    if not rename_plan:
        print("All state filenames are already correct.")
        return 0

    for source, destination in rename_plan:
        if args.dry_run:
            print(f"Would rename: {source.name} -> {destination.name}")
        else:
            source.rename(destination)
            print(f"Renamed: {source.name} -> {destination.name}")

    if args.dry_run:
        print("Dry run: no files were changed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
