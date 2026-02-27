import datetime


class NotionFilter:
    def __init__(self, rows) -> None:
        self.results = []
        self.rows = rows

    def name(self, name: str):
        results = self.results or self.rows
        self.results = [r for r in results if name in r["Engineers"]]
        return self

    def status(self, status: str):
        results = self.results or self.rows
        self.results = [r for r in results if r["Status"].lower() == status.lower()]
        return self

    def date_range(self, start: str, end: str | None = None):
        results = self.results or self.rows
        fmt = "%Y-%m-%d"
        start_date = datetime.datetime.strptime(start, fmt).date()
        end_date = datetime.datetime.strptime(end, fmt).date() if end else datetime.date.today()
        self.results = [
            r
            for r in results
            if start_date <= datetime.datetime.strptime(r["created"], "%B %d, %Y %I:%M %p").date() <= end_date
        ]
        return self
