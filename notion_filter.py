import datetime


class NotionFilter:
    def __init__(self, rows) -> None:
        self.rows = rows
        self.results = None  # None = unfiltered, [] = filtered to empty

    def name(self, name: str):
        results = self.rows if self.results is None else self.results
        self.results = [r for r in results if name in r["Engineers"]]
        return self

    def status(self, status: str):
        results = self.rows if self.results is None else self.results
        self.results = [r for r in results if r["Status"].lower() == status.lower()]
        return self

    def date_range(self, start: str, end: str):
        results = self.rows if self.results is None else self.results
        fmt = "%Y-%m-%d"
        start_date = datetime.datetime.strptime(start, fmt).date()
        end_date = datetime.datetime.strptime(end, fmt).date()
        self.results = [
            r
            for r in results
            if start_date <= datetime.datetime.strptime(r["created"], "%B %d, %Y %I:%M %p").date() <= end_date
        ]
        return self
