# Interface layout rule

- Keep application pages and forms within one viewport. Use compact sections and responsive grids instead of adding long explanatory blocks.
- Tables are the only content regions that scroll. Put tables in `TableContainer`; the shared theme caps their height and keeps their headers visible.
- When a form or information panel cannot fit, move the overflow into a dialog or drawer with its own clear title and actions. Do not make the whole page scroll to reveal secondary details.
- Show key outcomes first. Put metric definitions, raw JSON, logs, and other supporting detail behind a dialog, drawer, or expandable control.
- On narrow screens, stack controls and cards while preserving the same one-screen priority order.
