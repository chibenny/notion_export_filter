### Filter Notion Ticket CSV Export
---

A simple script to extract the tickets I've worked on for year-in-review. It isn't exhaustive by any means - but it's open to expansion and was fun to write.

##### Usage
Place your exported CSV's in `notion_tickets` then:
```bash
uv run main.py [-h] [--name NAME] [--status STATUS] [--start START] [--end END] [--export EXPORT]

# example
uv run main.py --name "Alison B"

- OR -

uv run main.py --name "Alison B" --status "Complete" --start "2024-12-01" --end "2025-12-31"
```
All you really need to run it is your name. `status` defaults to "Complete", `start` defaults to Today's date - 366, and `end` defaults to Today's date.

The results of the filter are written to a CSV file with a name of your choosing, or `results_export_<DEFAULT_START_DATE>_<DEFAULT_END_DATE>`.
**NOTE:** You do not add the extension when choosing an export name. This only spits out CSV's for the time being, so it already assumes the extension.
