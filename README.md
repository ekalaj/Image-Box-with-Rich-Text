# BuildTrack — House Construction Manager

A single-file, fully-offline project tracker for managing a custom home build
(set up for a Fort Lauderdale, FL project). No install, no server, no accounts.

## How to use
1. Open **`index.html`** in any web browser (double-click it).
2. That's it. All data is saved automatically in your browser (localStorage).

## Features
- **Dashboard** — overall % complete, budget snapshot, who's on site this week, what's next.
- **Schedule (Gantt)** — visual timeline of every task. Bars on the same days show
  trades working **side by side**. Group by phase or by trade, with a TODAY marker
  and automatic dependency-conflict warnings.
- **Tasks & Phases** — the build broken into phases (permitting → foundation → shell →
  roof → impact windows → MEP rough-ins → drywall → finishes → final), each task with
  status, % progress, dates, dependencies, cost and photos. Filter by phase/trade/status.
- **Trades directory** — contacts for every contractor (phone, email, license, color),
  with their assigned tasks.
- **Budget** — estimated vs. actual cost per phase and task, with variance.
- **Photos** — attach progress photos to any task (auto-downscaled to save space).
- **Backup / Restore** — export everything to a JSON file and re-import it (use this to
  move between computers or keep a safe copy).

## Notes
- Data lives only in *this* browser on *this* computer. Use **Backup** regularly.
- Comes preloaded with a realistic FL build (CBS block, hurricane tie-downs, impact
  windows, HVHZ tile roof, parallel MEP crews). Use **⚙ Project → Reset** to start fresh,
  or just edit/delete the sample tasks and trades.
