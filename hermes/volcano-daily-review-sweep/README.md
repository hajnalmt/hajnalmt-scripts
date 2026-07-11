# Volcano daily review sweep

Repo-backed helper for Hermes' daily Volcano maintainer review sweep.

## Purpose

`volcano_daily_review_candidates.py` collects a lightweight candidate list for `volcano-sh/volcano` PR review triage before the Hermes agent spends tokens and GitHub API calls on deep review.

The script is intentionally metadata-first:

- checks GitHub core rate limit at start and end;
- skips unchanged PRs already tracked as waiting on author feedback;
- separates deep-review candidates from overflow/lightweight triage;
- emits a hard review budget for the agent:
  - max 5 heavy PR inspections;
  - max 3 `gh pr diff` calls;
  - max 5 review-comment fetches;
  - disable deep review below 1000 remaining core GitHub API requests.

## Runtime requirements

- Python 3.11+.
- GitHub CLI (`gh`) authenticated as an account that can read `volcano-sh/volcano` PRs and comments.
- Local TODO note at `/home/hermes/work/private/notes/todos/volcano-maintainer.md` if author-waiting skip state should be preserved.

## Hermes cron wiring

The live Hermes cron job should call the repo-backed script directly:

```text
/home/hermes/work/private/hajnalmt-scripts/hermes/volcano-daily-review-sweep/volcano_daily_review_candidates.py
```

Current intended job:

- name: `Daily Volcano PR review sweep`
- schedule: `0 5 * * *`
- workdir: `/home/hermes/work/oss/volcano`
- delivery: `origin`

A safe copy/adapt example is in `cron-job.example.json`.

## Manual smoke check

From this directory:

```bash
./volcano_daily_review_candidates.py
```

The output should include `GitHub core rate limit before script`, `GitHub core rate limit after script`, and `Review budget for the agent`.
