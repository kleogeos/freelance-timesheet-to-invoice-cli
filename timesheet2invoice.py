#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone


def _entry_date(entry):
    """Date used for --since/--until filtering: prefer end, then start, then None (manual 'add' entries)."""
    raw = entry.get("end") or entry.get("start")
    if not raw:
        return None
    return datetime.fromisoformat(raw).date()


def _filter_entries(entries, project, since, until):
    out = []
    for e in entries:
        if project and e["project"] != project:
            continue
        if since or until:
            d = _entry_date(e)
            if d is None:
                # Entry has no timestamp (e.g. "add" without --note on a backfilled day) —
                # can't honor a date filter on it, so exclude rather than silently include.
                continue
            if since and d < since:
                continue
            if until and d > until:
                continue
        out.append(e)
    return out


def build_items(entries, rate, itemize):
    if not entries:
        return []
    if itemize:
        items = []
        for e in entries:
            d = _entry_date(e)
            date_part = f"{d.isoformat()} — " if d else ""
            note_part = f": {e['note']}" if e.get("note") else ""
            items.append({
                "description": f"{date_part}{e['project']}{note_part}",
                "qty": round(e["hours"], 2),
                "rate": rate,
            })
        return items
    by_project = {}
    for e in entries:
        by_project.setdefault(e["project"], 0.0)
        by_project[e["project"]] += e["hours"]
    return [
        {"description": project, "qty": round(hours, 2), "rate": rate}
        for project, hours in sorted(by_project.items(), key=lambda kv: -kv[1])
    ]


def main():
    p = argparse.ArgumentParser(
        prog="freelance-timesheet2invoice",
        description="Turn a freelance-time-cli timesheet.json into an invoice.json ready for freelance-invoice-cli. No dependencies.",
    )
    p.add_argument("timesheet", nargs="?", default="timesheet.json", help="Timesheet file from freelance-time-cli (default: timesheet.json)")
    p.add_argument("--rate", type=float, required=True, help="Hourly rate to bill at")
    p.add_argument("--project", help="Only include entries for this project (default: all projects, one line item each)")
    p.add_argument("--since", help="Only include entries on/after this date (YYYY-MM-DD)")
    p.add_argument("--until", help="Only include entries on/before this date (YYYY-MM-DD)")
    p.add_argument("--itemize", action="store_true", help="One invoice line per timesheet entry instead of one line per project")
    p.add_argument("--from-name", dest="from_name", required=True, help="Your name/business, goes in the invoice 'from' field")
    p.add_argument("--to", required=True, help="Client name, goes in the invoice 'to' field")
    p.add_argument("--invoice-number", default=None, help="Invoice number (default: INV-<today's date>)")
    p.add_argument("--date", default=None, help="Invoice date YYYY-MM-DD (default: today)")
    p.add_argument("--net", type=int, default=14, help="Payment terms in days, used to compute due_date if --due-date is not given (default: 14)")
    p.add_argument("--due-date", dest="due_date", default=None, help="Due date YYYY-MM-DD (default: invoice date + --net days)")
    p.add_argument("--tax-rate", dest="tax_rate", type=float, default=0, help="Tax rate as a percentage, e.g. 20 for 20%% (default: 0)")
    p.add_argument("--notes", default=None, help="Notes field on the invoice (default: 'Net <N>.')")
    p.add_argument("-o", "--output", help="Write invoice JSON to this file instead of stdout")
    args = p.parse_args()

    try:
        with open(args.timesheet) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Timesheet file not found: {args.timesheet}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"Could not parse {args.timesheet} as JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    since = datetime.strptime(args.since, "%Y-%m-%d").date() if args.since else None
    until = datetime.strptime(args.until, "%Y-%m-%d").date() if args.until else None

    entries = _filter_entries(data.get("entries", []), args.project, since, until)
    if not entries:
        print("No matching timesheet entries — nothing to invoice.", file=sys.stderr)
        sys.exit(1)

    items = build_items(entries, args.rate, args.itemize)

    today = datetime.now(timezone.utc).date()
    invoice_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else today
    due_date = datetime.strptime(args.due_date, "%Y-%m-%d").date() if args.due_date else invoice_date + timedelta(days=args.net)

    invoice = {
        "invoice_number": args.invoice_number or f"INV-{today.isoformat()}",
        "from": args.from_name,
        "to": args.to,
        "date": invoice_date.isoformat(),
        "due_date": due_date.isoformat(),
        "tax_rate": args.tax_rate,
        "items": items,
        "notes": args.notes or f"Net {args.net}. Late payments accrue 1.5% monthly interest after the due date.",
    }

    out = json.dumps(invoice, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(out + "\n")
        total_hours = sum(i["qty"] for i in items)
        print(f"Wrote {args.output}: {len(items)} line item(s), {total_hours:.2f}h total, ${total_hours * args.rate:,.2f} due.", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
