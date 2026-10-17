# freelance-timesheet-to-invoice-cli

[![Test CLI](https://github.com/kleogeos/freelance-timesheet-to-invoice-cli/actions/workflows/test.yml/badge.svg)](https://github.com/kleogeos/freelance-timesheet-to-invoice-cli/actions/workflows/test.yml)

Turn a [freelance-time-cli](https://github.com/kleogeos/freelance-time-cli) `timesheet.json` into an `invoice.json` ready for [freelance-invoice-cli](https://github.com/kleogeos/freelance-invoice-cli). No dependencies, no re-typing hours by hand.

```bash
python3 timesheet2invoice.py timesheet.json \
  --rate 60 --from-name "Jane Doe, Freelance Developer" --to "Acme Corp" \
  -o invoice.json

python3 invoice.py invoice.json -o invoice.html   # from freelance-invoice-cli
```

By default, one invoice line per project (hours summed). Use `--itemize` for one line per timesheet entry (with date and note), and `--project NAME` / `--since` / `--until` to invoice just part of the timesheet — handy for billing one client out of a shared timesheet file, or just this month's hours.

### Install (optional)

```bash
pip install git+https://github.com/kleogeos/freelance-timesheet-to-invoice-cli
freelance-timesheet2invoice timesheet.json --rate 60 --from-name "Jane Doe" --to "Acme Corp" -o invoice.json
```

### Usage

```
usage: timesheet2invoice.py [-h] --rate RATE [--project PROJECT] [--since SINCE] [--until UNTIL]
                             [--itemize] --from-name FROM_NAME --to TO [--invoice-number INVOICE_NUMBER]
                             [--date DATE] [--net NET] [--due-date DUE_DATE] [--tax-rate TAX_RATE]
                             [--notes NOTES] [-o OUTPUT]
                             [timesheet]
```

| Flag | What it does |
|---|---|
| `timesheet` | Path to the timesheet.json from freelance-time-cli (default: `timesheet.json`) |
| `--rate` | Hourly rate to bill at (required) |
| `--project` | Only include one project's entries (default: all, one line per project) |
| `--since` / `--until` | Only include entries in a date range (`YYYY-MM-DD`) — e.g. for monthly invoicing |
| `--itemize` | One invoice line per timesheet entry instead of one per project |
| `--from-name` / `--to` | Invoice "from"/"to" fields (required) |
| `--invoice-number`, `--date`, `--due-date`, `--net`, `--tax-rate`, `--notes` | Same fields as `freelance-invoice-cli`'s JSON format — `--due-date` defaults to invoice date + `--net` days (default 14) |
| `-o` / `--output` | Write to a file instead of stdout |

See [`example-timesheet.json`](example-timesheet.json) for a full example.

### Why this exists

`freelance-time-cli`'s own README says it "pairs with freelance-invoice-cli for turning the hours into an actual invoice" — but there was no actual converter, just two tools with compatible-but-not-connected JSON formats. This closes that gap: track hours all month, then one command away from a client-ready invoice, no manual re-entry of numbers.

Free web tools (no install): [invoice generator](https://kleogeos.github.io/freelancer-tools/invoice.html) · [rate calculator](https://kleogeos.github.io/freelancer-tools/rate-calculator.html)

Track the hours in the first place: [freelance-time-cli](https://github.com/kleogeos/freelance-time-cli) · Generate the actual invoice from the output: [freelance-invoice-cli](https://github.com/kleogeos/freelance-invoice-cli) · Work out what the rate should be: [freelance-rate-cli](https://github.com/kleogeos/freelance-rate-cli) · Chasing an overdue invoice? [freelance-late-fee-cli](https://github.com/kleogeos/freelance-late-fee-cli)

Need the paperwork beyond invoices — proposals, contracts, late-payment emails, client scripts? [Freelancer Starter Kit ($15, crypto or Telegram Stars, no KYC)](https://kleogeos.github.io/freelancer-tools/kit.html?src=cli-timesheet2invoice)

Free and will stay free. If it saved you time: [tip with crypto](https://kleogeos.github.io/freelancer-tools/donate.html).

## License

MIT — do whatever you want with it.
