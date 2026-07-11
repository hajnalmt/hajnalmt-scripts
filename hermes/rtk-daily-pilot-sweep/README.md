# RTK daily pilot sweep

Repo-backed helper for a Hermes pilot that watches [`rtk-ai/rtk`](https://github.com/rtk-ai/rtk), the Rust Token Killer project.

## Purpose

`rtk_daily_pilot_candidates.py` gathers a cheap, metadata-first list of PRs and issues worth looking at. The goal is a low-risk pilot, not maintainer automation:

- watch new/updated RTK PRs and issues;
- highlight high-priority/security/Windows/CLI topics;
- avoid burning GitHub API quota on every busy PR;
- avoid posting GitHub comments automatically;
- deliver a compact Telegram brief with suggested review/watch targets.

## Runtime requirements

- Python 3.11+.
- GitHub CLI (`gh`) authenticated with public repo read access.
- Optional local clone at `/home/hermes/work/oss/rtk` for manual/deep local review.

## Budget model

The script emits a hard budget for the agent:

- max 5 heavy PR inspections;
- max 5 issue triage inspections;
- max 3 `gh pr diff` calls;
- max 5 comment/review-comment fetches combined;
- disable deep review below 1000 remaining GitHub core API requests.

Overflow items should stay lightweight: metadata/checks/trend summary only.

## Hermes cron wiring

The live Hermes cron job should call the repo-backed script directly:

```text
/home/hermes/work/private/hajnalmt-scripts/hermes/rtk-daily-pilot-sweep/rtk_daily_pilot_candidates.py
```

Current intended pilot job:

- name: `Daily RTK pilot sweep`
- schedule: `15 6 * * *`
- workdir: `/home/hermes/work/oss/rtk`
- delivery: `origin`

A safe copy/adapt example is in `cron-job.example.json`.

## Manual smoke check

From this directory:

```bash
./rtk_daily_pilot_candidates.py
```

The output should include `GitHub core rate limit before script`, `GitHub core rate limit after script`, and `Review budget for the agent`.

## Local review caveats

The repo has its own `CLAUDE.md`. Key reminders:

- verify `pwd` and `git branch` before work;
- default branch is `develop`;
- this is `rtk-ai/rtk` Rust Token Killer, not the unrelated Rust Type Kit repo;
- full Rust quality gate is `cargo fmt --all && cargo clippy --all-targets && cargo test --all`.
