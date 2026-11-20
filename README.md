# Career radar (auto-updating)
1. Create a new GitHub repo (e.g. `career-radar`) and upload everything in this folder, including the hidden `.github` folder.
2. Settings > Pages > Deploy from branch > `main` / root. Your site: `https://<username>.github.io/career-radar/`.
3. Settings > Actions > General > Workflow permissions > Read and write.
4. Actions tab > "Update opportunities" > Run workflow once to test. After that it runs every hour by itself.

Hand-picked items live in `data/curated.json` (never auto-deleted). Auto-found items are added to `data/opportunities.json` and expire 30 days after their deadline.
To tune what gets picked up, edit the keyword lists and feeds at the top of `scripts/fetch_opportunities.py`.
