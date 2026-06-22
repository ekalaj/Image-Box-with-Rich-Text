# BuildTrack — Hosting & Cloud Sync Setup

This gets you to: **open `build.caligroup.org` on your phone or laptop, log in, and
see the same live data on both.** Three parts, ~15 minutes total.

- **Part A — Supabase** (the shared database + login) → ~5 min
- **Part B — Netlify** (hosts the page) → ~3 min
- **Part C — Subdomain** `build.caligroup.org` → ~5 min + DNS wait

You can use the app fully offline on one device *without* any of this. Cloud sync is
only needed to share data across devices.

---

## Part A — Supabase (shared data + login)

1. Go to **https://supabase.com** → sign up (free, no credit card) → **New project**.
   - Name it `caligroup-buildtrack`. Pick a strong database password (save it). Region: East US.
   - Wait ~2 min for it to provision.

2. **Create the data table.** Left sidebar → **SQL Editor** → **New query** → paste this and click **Run**:

   ```sql
   create table if not exists app_state (
     user_id uuid primary key references auth.users on delete cascade,
     data jsonb not null,
     updated_at timestamptz not null default now()
   );

   alter table app_state enable row level security;

   create policy "own row read"   on app_state for select using (auth.uid() = user_id);
   create policy "own row insert" on app_state for insert with check (auth.uid() = user_id);
   create policy "own row update" on app_state for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
   ```

3. **Create your login.** Left sidebar → **Authentication** → **Users** → **Add user** →
   **Create new user**. Enter the email + password you'll use (e.g. `build@caligroup.org`),
   and turn **ON** "Auto Confirm User". Click **Create user**.
   - This is the shared login. Everyone who should see the data signs in with these same
     credentials. (Want separate logins per person later? That's a future upgrade.)

4. **Grab your two keys.** Left sidebar → **Project Settings** (gear) → **API**:
   - **Project URL** — looks like `https://abcdwxyz.supabase.co`
   - **anon public** key — a long `eyJ…` string. (Safe to put in the browser — it only
     works alongside the row-level-security rules above.)

5. **Connect the app.** Open BuildTrack → click **☁ Sync** in the header → paste the
   **Project URL** and **anon public key**, enter your email + password from step 3,
   leave "Create this account" **unchecked**, click **Connect & sync**.
   - The header badge should turn green: **Synced ✓**.
   - Repeat this one-time connect on each device (phone + laptop). Same URL, key, email,
     password → same data everywhere.

---

## Part B — Netlify (host the page)

**Fastest (drag & drop):**
1. Put `index.html` in a folder by itself (rename a copy to `index.html` if needed).
2. Go to **https://app.netlify.com/drop** and drag the folder in. Done — you get a live
   URL like `https://random-name.netlify.app`.

**Or connect the GitHub repo (auto-deploys on every push):**
1. Netlify → **Add new site → Import an existing project → GitHub** → pick this repo.
2. Build command: *(leave blank)*. Publish directory: `/` (root). Deploy.

> Privacy note: the *page* is public, but it shows **no data until someone logs in**, and
> logins are gated by Supabase. That's the right model — protect the data, not the HTML.
> (Netlify's site-wide password is a paid add-on; you don't need it.)

---

## Part C — Subdomain `build.caligroup.org`

In Netlify: **Site configuration → Domain management → Add a custom domain** →
enter `build.caligroup.org` → Netlify shows you what DNS record to create.

Then at whoever hosts **caligroup.org**'s DNS (GoDaddy / Cloudflare / etc.), add:

| Type  | Name / Host | Value / Target              |
|-------|-------------|-----------------------------|
| CNAME | `build`     | `your-site-name.netlify.app`|

Save it. DNS takes 5 min–1 hr to propagate. Netlify auto-issues a free HTTPS certificate.
Then `https://build.caligroup.org` is live.

> If `caligroup.org` is on **Cloudflare**, set the CNAME record's proxy to **DNS only**
> (grey cloud) so Netlify can issue the certificate, or move the whole domain to
> Netlify DNS and let it manage everything.

---

## Use it like an app on your phone
Open `build.caligroup.org` in the phone browser → **Share → Add to Home Screen**. You get
a BuildTrack icon that opens full-screen, just like a native app.

---

## How sync behaves (good to know)
- Every change saves locally **instantly**, then pushes to the cloud about a second later.
- Each device pulls the latest every **20 seconds** and whenever you switch back to the tab.
- It's **last-write-wins** at the whole-project level: if two people edit the *exact same
  moment*, the later save wins. Fine for an owner + GC; just don't both edit the identical
  field at the identical second.
- Works offline: changes queue locally and push next time you're online.
- **Photos** live inside the synced data. They're auto-shrunk, but if you attach hundreds,
  the dataset gets large — keep an eye on it, or lean on the **⬇ Backup** button for
  archives. (We can move photos to dedicated cloud storage later if you need volume.)

## Backups
**⬇ Backup** downloads every project as one JSON file — great to drop in pCloud as an
offsite safety copy. **⬆ Restore** loads one back. Do this occasionally regardless of cloud.
