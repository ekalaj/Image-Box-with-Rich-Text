# BuildTrack — House Construction Manager

A single-file project tracker for managing custom home builds. Tracks **multiple
projects** (starts with **900 Guava**), runs fully offline on one device, and can
optionally sync across your phone + laptop via a free cloud account.

## How to use
1. Open **`index.html`** in any web browser (double-click it).
2. All data saves automatically in your browser.
3. To share live data across devices, see **[SETUP.md](SETUP.md)** (Supabase + Netlify +
   the `build.caligroup.org` subdomain).

## Multiple projects
- The header **project dropdown** switches between builds.
- **＋ Project** adds a new one — it starts with the standard Florida phase template and
  trade directory, ready for you to add tasks.
- Rename / delete a project from **⚙ Settings**.

## Cloud sync across phone + laptop
The **☁ Sync** button connects the app to a free Supabase backend behind a login, so both
devices share live data (auto-saves, pulls every 20s). Full walkthrough in **SETUP.md**.
Without it, the app still works — data just stays on the one device.

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
- Without cloud sync, data lives only in *this* browser on *this* device — use **Backup**
  regularly (drop the JSON in pCloud for an offsite copy).
- The **900 Guava** sample is a realistic FL build (CBS block, hurricane tie-downs, impact
  windows, HVHZ tile roof, parallel MEP crews). Edit/delete the sample items, or
  **⚙ Settings → Erase ALL projects** to start clean.
