# LedgerX Manufacturing (`ledgerx_manufacturing`)

Manufacturing as its own LedgerX module: one desktop tile (**Factory**) that holds production, quality, reports and setup, with barcode scanning in the operations, stages and production lines.

It is a layer over the standard Work Order, Job Card, BOM, Workstation and Quality Inspection documents. It does not replace them: every scan calls the standard methods, so costing, stock and accounting stay the standard ones.

## What it adds

| Area | What |
|---|---|
| Desktop | A **Factory** tile with its own sidebar: Production, Quality (all quality documents), Reports, Planning, Setup. The standard Manufacturing and Quality tiles are hidden (their pages still open from the new sidebar). |
| Production lines | **Production Line** with its ordered stations and target output per hour; each Workstation gets a station barcode and a line. |
| Operator screen | `/factory`, built for a phone or a keyboard-wedge scanner. Scan an employee badge, a station, a Job Card or a Work Order; start, pause, resume and finish; report good and scrap quantity with a reason; open the quality inspection. |
| Materials and product | On a Work Order, scan raw materials (checked against the required items and quantities), then post one Material Transfer; receive the finished product as a Manufacture entry. |
| Scan log | Every action is kept in **Production Scan** (who, when, where, how many). |
| Quality | Per-operation switch of the standard Work Order plus an optional factory-wide rule: no Job Card is submitted without an accepted inspection. A Quality Check button on the operator screen creates the inspection. |
| Waste | **Waste Reason** list; scrap is booked as the Job Card process loss and logged with its reason. |
| Reports | Line Efficiency, Waste Report, Operator Productivity, Production Cost (actual unit cost against the BOM). |
| Labels | Print Code 128 labels for Job Card, Work Order, Workstation, Employee, Item, Batch and Production Line from the form or from a list selection. |

## Scanning

Barcodes are plain values: the Job Card and Work Order name, the station barcode (`WS-0001`), the line barcode (`LN-0001`), the employee ID or the optional badge code, the item barcode or item code, the batch name. A value like `ITEM-01*12` means quantity 12. Any USB or Bluetooth scanner that types the code and presses Enter works; Chrome on Android can also scan with the camera.

## Settings (Factory Settings)

Operator must scan a badge, station must be scanned, submit the Job Card when everything is done, default waste reason, beep, and the quality rule.

## Install

See `docs/INSTALL.md`. Requires the standard accounting and stock app (`erpnext`).

## Limits to know

- The Stock Entry steps (post material issue, receive product) use the standard `make_stock_entry`; items that need serial or batch bundles, or work orders that require Job Cards before manufacture, return the standard error to the screen.
- The label page and screen need the browser to reach the server only; the barcode library is bundled.
- Camera scanning needs a browser with the BarcodeDetector API (Chrome on Android).

## Tests

`python3 -m unittest ledgerx_manufacturing.tests.test_logic` runs the pure rules (quantity split, scrap and efficiency, cost variance, issue limits). Database-dependent code was not run outside a real site.
