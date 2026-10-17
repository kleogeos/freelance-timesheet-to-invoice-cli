import json
import subprocess
import sys
import tempfile
import os

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timesheet2invoice.py")

TIMESHEET = {
    "running": None,
    "entries": [
        {"project": "acme", "start": "2026-10-01T09:00:00+00:00", "end": "2026-10-01T12:30:00+00:00", "hours": 3.5, "note": "logo design"},
        {"project": "acme", "start": "2026-10-02T09:00:00+00:00", "end": "2026-10-02T11:00:00+00:00", "hours": 2.0, "note": "revisions"},
        {"project": "beta", "start": "2026-10-01T13:00:00+00:00", "end": "2026-10-01T15:00:00+00:00", "hours": 2.0, "note": ""},
        {"project": "acme", "start": None, "end": None, "hours": 1.0, "note": "backfill, no timestamp"},
    ],
}


def _write_timesheet(path, data=None):
    with open(path, "w") as f:
        json.dump(data if data is not None else TIMESHEET, f)


def run(args, cwd):
    return subprocess.run(
        [sys.executable, SCRIPT] + args,
        cwd=cwd, capture_output=True, text=True,
    )


def test_one_line_per_project_by_default():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "timesheet.json")
        _write_timesheet(path)
        r = run([path, "--rate", "50", "--from-name", "Jane", "--to", "Acme Corp"], d)
        assert r.returncode == 0, r.stderr
        invoice = json.loads(r.stdout)
        descriptions = {i["description"]: i["qty"] for i in invoice["items"]}
        assert descriptions == {"acme": 6.5, "beta": 2.0}
        assert all(i["rate"] == 50 for i in invoice["items"])


def test_project_filter():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "timesheet.json")
        _write_timesheet(path)
        r = run([path, "--rate", "50", "--project", "beta", "--from-name", "Jane", "--to", "Acme"], d)
        assert r.returncode == 0, r.stderr
        invoice = json.loads(r.stdout)
        assert len(invoice["items"]) == 1
        assert invoice["items"][0]["description"] == "beta"
        assert invoice["items"][0]["qty"] == 2.0


def test_itemize_includes_date_and_note():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "timesheet.json")
        _write_timesheet(path)
        r = run([path, "--rate", "50", "--itemize", "--from-name", "Jane", "--to", "Acme"], d)
        assert r.returncode == 0, r.stderr
        invoice = json.loads(r.stdout)
        # 4 entries total, but one has no timestamp and gets excluded only by date filters,
        # not by itemize itself -- itemize alone should keep all 4.
        assert len(invoice["items"]) == 4
        dated = [i for i in invoice["items"] if i["description"].startswith("2026-10-01 — acme")]
        assert len(dated) == 1
        assert "logo design" in dated[0]["description"]


def test_since_until_filters_by_date_and_drops_timestampless_entries():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "timesheet.json")
        _write_timesheet(path)
        r = run([path, "--rate", "50", "--since", "2026-10-02", "--from-name", "Jane", "--to", "Acme"], d)
        assert r.returncode == 0, r.stderr
        invoice = json.loads(r.stdout)
        # Only the 2026-10-02 acme entry (2h) qualifies; the untimestamped backfill entry
        # and the 10-01 entries are excluded.
        assert invoice["items"] == [{"description": "acme", "qty": 2.0, "rate": 50}]


def test_no_matching_entries_exits_nonzero():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "timesheet.json")
        _write_timesheet(path, {"running": None, "entries": []})
        r = run([path, "--rate", "50", "--from-name", "Jane", "--to", "Acme"], d)
        assert r.returncode != 0
        assert "nothing to invoice" in r.stderr.lower()


def test_due_date_defaults_to_net_14_days_after_invoice_date():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "timesheet.json")
        _write_timesheet(path)
        r = run([path, "--rate", "50", "--date", "2026-10-01", "--from-name", "Jane", "--to", "Acme"], d)
        assert r.returncode == 0, r.stderr
        invoice = json.loads(r.stdout)
        assert invoice["date"] == "2026-10-01"
        assert invoice["due_date"] == "2026-10-15"


def test_output_file_matches_freelance_invoice_cli_schema():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "timesheet.json")
        out_path = os.path.join(d, "invoice.json")
        _write_timesheet(path)
        r = run([path, "--rate", "50", "--from-name", "Jane", "-o", out_path, "--to", "Acme"], d)
        assert r.returncode == 0, r.stderr
        with open(out_path) as f:
            invoice = json.load(f)
        required = {"invoice_number", "from", "to", "date", "due_date", "tax_rate", "items", "notes"}
        assert required.issubset(invoice.keys())
        for item in invoice["items"]:
            assert {"description", "qty", "rate"}.issubset(item.keys())


if __name__ == "__main__":
    failures = 0
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL: {t.__name__}: {e}")
    if failures:
        print(f"{failures} failure(s)")
        sys.exit(1)
    print(f"All {len(tests)} tests passed")
