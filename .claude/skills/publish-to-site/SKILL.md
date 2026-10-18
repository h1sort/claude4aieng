---
name: publish-to-site
description: Publish or refresh the live copy of the "Tool use sin abstracciones" deck at h1sort.com/claude4aieng by syncing a public build into the h1sort-website repo. Use after any edit to the deck, or when asked to publish, deploy, refresh or update the slides on the site.
---

# Publish the deck to h1sort.com/claude4aieng

**This repo is the source of truth.** `h1sort-website` only holds a generated public copy. Never edit the deck inside the site repo.

```
claude4aieng/deck/src/**  ──assemble.mjs --public──▶  h1sort-website/public/claude4aieng/index.html  ──▶  h1sort.com/claude4aieng/
cover (slide 1) 1200×630 JPEG                    ──▶  h1sort-website/public/claude4aieng/og.jpg
```

## Steps

1. **Deck committed here.** `node deck/tools/assemble.mjs --expect 40:00` and `node deck/tools/shot.mjs deck/tool-use.html` pass; commit and push `main`.
2. **Public build:** `node deck/tools/assemble.mjs --expect 40:00 --public --out <scratch>/index.html`. It strips every `<aside class="notes">` and adds `data-public` (no control bar; N, P, ? disabled). Check: `grep -c 'class="notes"'` is 0.
3. **OG image** only if slide 1 changed: render `?still=1&solo=1&slide=1` at 1200×630 with Playwright (`deck/node_modules`), JPEG quality ~82, keep it under 300 KB.
4. **Site repo:** `git checkout main && git pull`, new branch `chore/refresh-claude4aieng`, copy the files into `public/claude4aieng/`, `npm ci && npm run build`, confirm `cmp dist/claude4aieng/index.html public/claude4aieng/index.html`.
5. **Smoke test real routing:** `npx wrangler dev --port 8799` in the background with a `timeout`; `/claude4aieng` → 307, `/claude4aieng/` → 200, `/snowflake/` and `/gbm-ai/` still 200. Stop it with `timeout`, not `pkill -f 'wrangler dev'` (that pattern matches the shell running it and kills your own command).
6. **Commit only the deck paths** (`public/claude4aieng`, plus `astro.config.mjs` / `public/llms.txt` if changed). Never `git add -A`.
7. **Any branch push deploys production** (Workers Builds, ~2.5 min). Push, open the PR and merge it right away so `main` matches what is live; confirm the "Workers Builds" check on the merge commit succeeded.

## Lessons log

- 2026-10-18 · `main` had been behind production since 2026-10-13: the Snowflake talk was deployed from `feat/snowflake-world-tour` (branch push = deploy) and never merged. Merged as PR #20 (tree identical to the deployed branch, no visible change). Rule: always merge the same day a branch deploys.
- 2026-10-18 · First mount of `/claude4aieng/` via PR #21 (`039a04b`), from claude4aieng `b1b7e43`. Build and deploy checks succeeded.
- 2026-10-18 · Branch deletion is blocked from Claude Code cloud sessions (API and git push both 403); delete merged branches from the GitHub UI.
- 2026-10-18 · Refresh via PR #22 (`3aaff2f`) from claude4aieng `2d87bab` after the live dry run (measured table on slide 16). Deploy succeeded.
- 2026-10-18 · To check the `paso-*` branches on GitHub, use `git ls-remote origin 'paso-*'` or fetch them explicitly (`git fetch origin '+refs/heads/paso-*:refs/remotes/origin/paso-*'`): a plain `git fetch` in this shallow clone only updates `main` and leaves stale `origin/paso-*` refs.
- 2026-10-18 · Refresh via PR #23 (`403f357`) from claude4aieng `508bb0a`: Rotura #1b slide, 18 slides. Deploy succeeded.
