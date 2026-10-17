# Kart Atlas — GitHub + Cloudflare, zero-monthly-fee setup

## Step 1 — Create the GitHub public repository

1. Sign in to https://github.com/ and choose **New repository**.
2. Name it `kart-atlas`, select **Public**, and don't add starter README/license files (they're in this package).
3. From your desktop, unzip `Kart_Atlas_GitHub_Ready.zip` into a folder. **Upload the contents, not the ZIP itself**, to your new GitHub repository. You can use GitHub Desktop or git CLI. An empty GitHub repository is required for the CLI commands below.
4. From a terminal inside that extracted folder, run:

   ```bash
   git init
   git branch -M main
   git add .
   git commit -m "Launch Kart Atlas with source monitoring"
   git remote add origin https://github.com/YOUR_USERNAME/kart-atlas.git
   git push -u origin main
   ```

   Git may prompt you to authenticate. GitHub accounts support the Git Credential Manager / browser sign-in; do not paste a personal access token into chat.

Alternatively, **connect GitHub within ChatGPT** and allow the connected app to work with your repository, if it supports these actions. The GitHub connection requires your explicit authorization and has not been completed here.

## Step 2 — Connect Cloudflare Pages

1. Create a free account at https://dash.cloudflare.com/.
2. Go to **Workers & Pages > Create application > Pages > Connect to Git**.
3. Authorize your GitHub account and choose `kart-atlas`.
4. Use **Framework preset: None**, **Production branch: main**, **Build output directory: site**, and **Build command: blank** (or `exit 0` if Cloudflare requests one). Leave advanced root directory empty / repository root.
5. Deploy. You'll receive a public HTTPS URL similar to `your-project.pages.dev`. The exact address depends on availability.

> Important: if an older Kart Atlas site was created with **Direct Upload**, Cloudflare says it cannot be converted to Git integration. Create a **new Git-integrated Pages project**, and share the new public link.

## Step 3 — Activate daily monitoring

1. In your GitHub repo, open **Actions**. Allow the repository's workflows if prompted.
2. Choose **Refresh North American kart calendar** > **Run workflow** to run the initial check. The workflow also runs daily at 13:17 UTC (scheduled GitHub runs can be delayed).
3. In **Actions**, check the run status. If push fails due to token restrictions, the repository/organization administrator must allow workflow write permissions. Workflow needs `contents: write`; optional review issues need `issues: write`.
4. The first successful run establishes a *baseline*. The next genuine organizer page change creates a review signal. Two public ICS exports have automated ingestion enabled but can fail depending on live access/robots rules; don't assume they work until the logs confirm them.
5. The workflow updates `site/monitor_status.json` and commits results. Cloudflare automatically republishes every successful commit.

## Step 4 — Install on phone

On Android, open your public `pages.dev` link in Chrome and use **⋮ > Add to Home screen / Install app**. On iPhone, open the URL in Safari > Share > Add to Home Screen. A domain purchase and app-store registration are unnecessary.

## Keep it healthy for free

- Check GitHub **Actions** run logs about once a month. Failed sources are visible in `reports/latest.json` and an aggregate is displayed in the app after a successful run.
- If a page changes but can't be parsed reliably, review the GitHub issue, verify races on the organizer's site and add correct rows to `data/races.csv`. A simple CSV edit triggers Cloudflare deployment only after the generated data is rebuilt; run the workflow manually once after the edit.
- Add official calendar endpoints to `data/monitor_sources.json`, ideally ICS feeds. Set `auto_import: false` for a new feed until it's tested against real responses. Many websites never publish a structured feed.
- A public GitHub repository using standard GitHub-hosted runners currently has no Actions minute charge. Cloudflare Pages free plan has build limits; running this workflow once daily should be far below 500 builds/month.
- GitHub can deactivate scheduled workflows after prolonged repository inactivity. Monitor Actions periodically and re-enable if necessary.
- Do not commit account passwords, tokens or personal information. Never pay to access protected or private organizer APIs without explicitly evaluating the cost.

## Common troubleshooting

| Symptom | Action |
|---|---|
| GitHub run fails on git push | Check Actions workflow permissions and repo branch protection. |
| Some club URLs fail or show robots disallowed | Respect the restriction. Use the source manually, or ask organizers to publish public ICS/JSON feeds. |
| Cloudflare publishes an old race list | Check the latest Actions run, changed `site/events.json`, and Pages build status. The PWA fetches online first when connected. |
| 2027 club dates aren't showing | Many clubs haven't published them. An HTML change watcher can't safely invent future dates. |
| Auto-import missed a race | Add verified row to CSV and/or add a tested parser for that club. |
| Cloudflare Pages project is direct-upload based | Create a **new** Git-integrated project. |

**No external account was created and no live site was deployed during packaging.**
