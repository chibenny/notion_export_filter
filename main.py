import argparse
import csv
import datetime
from pathlib import Path

from notion_filter import NotionFilter

CSV_DIR = Path("notion_tickets")
DEFAULT_START_DATE = str(
    datetime.datetime.today().date() - datetime.timedelta(days=366)
)
DEFAULT_END_DATE = str(datetime.datetime.today().date())
DEFAULT_EXPORT_NAME = f"results_export_{DEFAULT_START_DATE}_{DEFAULT_END_DATE}"


def unpack(filename):
    with open(filename, "r") as csv_file:
        return list(csv.DictReader(csv_file))


def export(results: list[dict[str, str]], filename: str | None = None):
    filename = f"{filename or DEFAULT_EXPORT_NAME}.csv"
    with open(filename, "w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)


def remove_duplicates(rows: list[dict[str, str]]):
    unique = {r["ID"]: r for r in rows}.values()
    return sorted(unique, key=lambda r: r["ID"])


def fetch_args():
    parser = argparse.ArgumentParser(
        description="Filter and export Notion ticket CSVs."
    )
    parser.add_argument(
        "--name", default="", help="Filter by Engineer name (e.g. 'Benny C')"
    )
    parser.add_argument(
        "--status",
        default="Complete",
        help="Filter by ticket status (default: Complete)",
    )
    parser.add_argument(
        "--start",
        default=DEFAULT_START_DATE,
        help="Start date in YYYY-MM-DD format (default: Today - 366)",
    )
    parser.add_argument(
        "--end",
        default=DEFAULT_END_DATE,
        help="End date in YYYY-MM-DD format (default: Today)",
    )
    parser.add_argument(
        "--export",
        default=DEFAULT_EXPORT_NAME,
        help="Name of the export file `without` the extension (e.g. 'review-2025-2026')",
    )
    return parser.parse_args()


def main():
    args = fetch_args()
    rows = []
    for path in CSV_DIR.glob("*.csv"):
        rows = rows + unpack(path)

    # preflight check
    if not args.name:
        print("Oops - don't forget to add your name!")
        return

    if not rows:
        print("Oops - please add some Notion Export CSV's to `notion_tickets`")
        return

    n_filter = NotionFilter(rows)
    year_in_review = (
        n_filter.name(args.name).status(args.status).date_range(args.start, args.end)
    ).results

    if not year_in_review:
        print("No results found matching your filters.")
        return

    export(remove_duplicates(year_in_review))


if __name__ == "__main__":
    main()
