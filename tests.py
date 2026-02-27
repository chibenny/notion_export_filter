import csv
import os
import tempfile
import unittest

from notion_filter import NotionFilter
from main import export, remove_duplicates, unpack

FULL_HEADER = "Name,Created by,Description/Use Case,Due,Engineers,ID,Priority,Product,Service,Sprint 1,Status,Type,created"

SAMPLE_ROWS = [
    {
        "Name": "Artist Search Broken",
        "Created by": "Duke Ellington",
        "Description/Use Case": "",
        "Due": "",
        "Engineers": "Jimmie Dean, Duke Ellington",
        "ID": "301",
        "Priority": "P2",
        "Product": "Catalog",
        "Service": "Backend",
        "Sprint 1": "Sprint 34",
        "Status": "Complete",
        "Type": "Bug",
        "created": "April 12, 2024 2:01 PM",
    },
    {
        "Name": "Playlist Sync Failing",
        "Created by": "Duke Ellington",
        "Description/Use Case": "",
        "Due": "",
        "Engineers": "Duke Ellington",
        "ID": "302",
        "Priority": "P1",
        "Product": "Player",
        "Service": "Backend",
        "Sprint 1": "Sprint 35",
        "Status": "In Progress",
        "Type": "Bug",
        "created": "March 10, 2025 9:00 AM",
    },
    {
        "Name": "Add Dark Mode",
        "Created by": "Carol D",
        "Description/Use Case": "",
        "Due": "",
        "Engineers": "Carol D",
        "ID": "303",
        "Priority": "P3",
        "Product": "UI",
        "Service": "Frontend",
        "Sprint 1": "Sprint 36",
        "Status": "Complete",
        "Type": "Feature",
        "created": "July 4, 2024 12:00 PM",
    },
    {
        "Name": "Onboarding Redesign",
        "Created by": "Jimmie Dean",
        "Description/Use Case": "",
        "Due": "",
        "Engineers": "Alice A",
        "ID": "304",
        "Priority": "P2",
        "Product": "Onboarding",
        "Service": "Frontend",
        "Sprint 1": "Sprint 37",
        "Status": "complete",
        "Type": "Task",
        "created": "December 31, 2025 11:59 PM",
    },
]


class TestNotionFilterName(unittest.TestCase):
    def test_filters_by_exact_name(self):
        results = NotionFilter(SAMPLE_ROWS).name("Duke Ellington").results
        self.assertEqual(len(results), 2)
        self.assertTrue(all("Duke Ellington" in r["Engineers"] for r in results))

    def test_filters_by_partial_name(self):
        results = NotionFilter(SAMPLE_ROWS).name("Duke").results
        self.assertEqual(len(results), 2)

    def test_no_match_returns_empty(self):
        results = NotionFilter(SAMPLE_ROWS).name("Zork Z").results
        self.assertEqual(results, [])

    def test_returns_self_for_chaining(self):
        f = NotionFilter(SAMPLE_ROWS)
        self.assertIs(f.name("Duke Ellington"), f)


class TestNotionFilterStatus(unittest.TestCase):
    def test_filters_by_status(self):
        results = NotionFilter(SAMPLE_ROWS).status("In Progress").results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["ID"], "302")

    def test_case_insensitive(self):
        # "301" Complete, "303" Complete, "304" complete — all three match
        lower = NotionFilter(SAMPLE_ROWS).status("complete").results
        upper = NotionFilter(SAMPLE_ROWS).status("COMPLETE").results
        self.assertEqual(len(lower), 3)
        self.assertEqual(len(lower), len(upper))

    def test_no_match_returns_empty(self):
        results = NotionFilter(SAMPLE_ROWS).status("Blocked").results
        self.assertEqual(results, [])

    def test_returns_self_for_chaining(self):
        f = NotionFilter(SAMPLE_ROWS)
        self.assertIs(f.status("Complete"), f)


class TestNotionFilterDateRange(unittest.TestCase):
    def test_filters_within_range(self):
        results = NotionFilter(SAMPLE_ROWS).date_range("2025-01-01", "2025-12-31").results
        ids = [r["ID"] for r in results]
        self.assertIn("302", ids)   # March 10, 2025
        self.assertIn("304", ids)   # December 31, 2025
        self.assertNotIn("301", ids)  # April 2024 — out of range
        self.assertNotIn("303", ids)  # July 2024 — out of range

    def test_excludes_outside_range(self):
        results = NotionFilter(SAMPLE_ROWS).date_range("2024-01-01", "2024-12-31").results
        ids = [r["ID"] for r in results]
        self.assertEqual(len(results), 2)
        self.assertIn("301", ids)  # April 12, 2024
        self.assertIn("303", ids)  # July 4, 2024

    def test_inclusive_boundaries(self):
        results = NotionFilter(SAMPLE_ROWS).date_range("2024-04-12", "2024-04-12").results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["ID"], "301")

    def test_no_match_returns_empty(self):
        results = NotionFilter(SAMPLE_ROWS).date_range("2020-01-01", "2020-12-31").results
        self.assertEqual(results, [])

    def test_returns_self_for_chaining(self):
        f = NotionFilter(SAMPLE_ROWS)
        self.assertIs(f.date_range("2025-01-01", "2025-12-31"), f)


class TestNotionFilterChaining(unittest.TestCase):
    def test_name_then_status(self):
        # Duke worked on 2 tickets but only 1 is Complete
        results = NotionFilter(SAMPLE_ROWS).name("Duke Ellington").status("Complete").results
        self.assertEqual(len(results), 1)
        self.assertIn("Duke Ellington", results[0]["Engineers"])
        self.assertEqual(results[0]["Status"].lower(), "complete")

    def test_full_chain(self):
        results = (
            NotionFilter(SAMPLE_ROWS)
            .name("Duke Ellington")
            .status("Complete")
            .date_range("2024-01-01", "2024-12-31")
            .results
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["ID"], "301")

    def test_chain_yielding_no_results(self):
        results = (
            NotionFilter(SAMPLE_ROWS)
            .name("Carol D")
            .status("In Progress")
            .results
        )
        self.assertEqual(results, [])

    def test_chain_after_empty_does_not_reset(self):
        # If name() filters to empty, status() should not fall back to all rows
        results = (
            NotionFilter(SAMPLE_ROWS)
            .name("Zork Z")
            .status("Complete")
            .results
        )
        self.assertEqual(results, [])


class TestRemoveDuplicates(unittest.TestCase):
    def test_removes_duplicate_ids(self):
        rows = [
            {**SAMPLE_ROWS[0]},
            {**SAMPLE_ROWS[0]},  # exact duplicate
            {**SAMPLE_ROWS[1]},
        ]
        self.assertEqual(len(remove_duplicates(rows)), 2)

    def test_preserves_all_unique_rows(self):
        self.assertEqual(len(remove_duplicates(SAMPLE_ROWS)), len(SAMPLE_ROWS))

    def test_sorted_by_id(self):
        rows = [
            {**SAMPLE_ROWS[2]},  # 303
            {**SAMPLE_ROWS[0]},  # 301
            {**SAMPLE_ROWS[1]},  # 302
        ]
        result = remove_duplicates(rows)
        self.assertEqual([r["ID"] for r in result], ["301", "302", "303"])

    def test_duplicate_keeps_last_seen(self):
        first = {**SAMPLE_ROWS[0]}                          # Engineers: "Jimmie Dean, Duke Ellington"
        second = {**SAMPLE_ROWS[0], "Engineers": "Alice A"} # same ID, different engineers
        result = remove_duplicates([first, second])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Engineers"], "Alice A")


class TestUnpack(unittest.TestCase):
    def test_reads_csv_as_list_of_dicts(self):
        content = (
            f"{FULL_HEADER}\n"
            'Artist Search Broken,Duke Ellington,,,Jimmie Dean,301,P2,Catalog,Backend,Sprint 34,Complete,Bug,"April 12, 2024 2:01 PM"\n'
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(content)
            tmp_path = f.name
        try:
            result = unpack(tmp_path)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["ID"], "301")
            self.assertEqual(result[0]["Engineers"], "Jimmie Dean")
        finally:
            os.unlink(tmp_path)

    def test_empty_csv_returns_empty_list(self):
        content = f"{FULL_HEADER}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(content)
            tmp_path = f.name
        try:
            result = unpack(tmp_path)
            self.assertEqual(result, [])
        finally:
            os.unlink(tmp_path)

    def test_multiple_rows(self):
        content = (
            f"{FULL_HEADER}\n"
            'Artist Search Broken,Duke Ellington,,,Jimmie Dean,301,P2,Catalog,Backend,Sprint 34,Complete,Bug,"April 12, 2024 2:01 PM"\n'
            'Playlist Sync Failing,Duke Ellington,,,Duke Ellington,302,P1,Player,Backend,Sprint 35,In Progress,Bug,"March 10, 2025 9:00 AM"\n'
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(content)
            tmp_path = f.name
        try:
            result = unpack(tmp_path)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[1]["ID"], "302")
        finally:
            os.unlink(tmp_path)


class TestExport(unittest.TestCase):
    def test_writes_rows_to_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            name = os.path.join(tmpdir, "output")
            export([SAMPLE_ROWS[0]], name)
            with open(f"{name}.csv", "r") as f:
                written = list(csv.DictReader(f))
        self.assertEqual(len(written), 1)
        self.assertEqual(written[0]["ID"], "301")
        self.assertEqual(written[0]["Engineers"], "Jimmie Dean, Duke Ellington")

    def test_writes_header_row(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            name = os.path.join(tmpdir, "output")
            export([SAMPLE_ROWS[0]], name)
            with open(f"{name}.csv", "r") as f:
                header = f.readline().strip()
        self.assertEqual(header, FULL_HEADER)

    def test_appends_csv_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            name = os.path.join(tmpdir, "output")
            export([SAMPLE_ROWS[0]], name)
            self.assertTrue(os.path.exists(f"{name}.csv"))

    def test_writes_multiple_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            name = os.path.join(tmpdir, "output")
            export(SAMPLE_ROWS, name)
            with open(f"{name}.csv", "r") as f:
                written = list(csv.DictReader(f))
        self.assertEqual(len(written), len(SAMPLE_ROWS))


if __name__ == "__main__":
    unittest.main()
