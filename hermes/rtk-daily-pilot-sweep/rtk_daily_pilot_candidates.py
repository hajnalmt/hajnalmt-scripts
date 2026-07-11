#!/usr/bin/env python3
"""Collect RTK pilot review/triage candidates for a daily Hermes sweep."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

OWNER_REPO = "rtk-ai/rtk"
REVIEWER = "hajnalmt"
DEFAULT_BRANCH = "develop"
MAX_ITEMS = 100
TODO_PATH = Path("/home/hermes/work/private/notes/todos/rtk-pilot.md")
MAX_HEAVY_PR_INSPECTIONS = 5
MAX_ISSUE_TRIAGE_INSPECTIONS = 5
MAX_DIFF_FETCHES = 3
MAX_COMMENT_FETCHES = 5
MIN_CORE_RATE_REMAINING_FOR_DEEP_REVIEW = 1000
PRIORITY_LABELS = {"priority:critical", "priority:high", "bug", "wrong-base"}
WATCH_LABELS = {"area:cli", "area:security", "platform:windows", "help wanted", "good first issue"}

_GH_API_CALLS = 0


def gh_json(args: list[str], *, optional: bool = False) -> str:
    global _GH_API_CALLS
    last_error = None
    for attempt in range(2):
        try:
            _GH_API_CALLS += 1
            return subprocess.check_output(["gh", *args], text=True, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(2)
                continue
    if optional:
        print(f"Warning: failed optional gh {' '.join(args)} request: {last_error}", file=sys.stderr)
        return ""
    raise last_error  # type: ignore[misc]


def gh_api(path: str, *, optional: bool = False):
    out = gh_json(["api", path, "--paginate"], optional=optional)
    if not out:
        return []
    chunks = []
    decoder = json.JSONDecoder()
    text = out.strip()
    while text:
        obj, idx = decoder.raw_decode(text)
        chunks.append(obj)
        text = text[idx:].strip()
    if len(chunks) == 1:
        return chunks[0]
    merged = []
    for chunk in chunks:
        if isinstance(chunk, list):
            merged.extend(chunk)
        else:
            merged.append(chunk)
    return merged


def rate_limit_snapshot() -> dict:
    data = json.loads(gh_json(["api", "rate_limit"], optional=True) or "{}")
    core = (data.get("resources") or {}).get("core") or data.get("rate") or {}
    graphql = (data.get("resources") or {}).get("graphql") or {}
    search = (data.get("resources") or {}).get("search") or {}
    return {
        "core_limit": core.get("limit"),
        "core_used": core.get("used"),
        "core_remaining": core.get("remaining"),
        "core_reset": core.get("reset"),
        "graphql_remaining": graphql.get("remaining"),
        "search_remaining": search.get("remaining"),
    }


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def label_names(item: dict) -> set[str]:
    return {label.get("name", "") for label in item.get("labels") or []}


def is_interesting_issue(issue: dict, since: datetime) -> bool:
    labels = label_names(issue)
    created = parse_ts(issue["created_at"])
    updated = parse_ts(issue["updated_at"])
    if created >= since or updated >= since:
        return True
    return bool(labels & (PRIORITY_LABELS | WATCH_LABELS))


def pr_reasons(pr: dict, since: datetime) -> list[str]:
    labels = label_names(pr)
    created = parse_ts(pr["created_at"])
    updated = parse_ts(pr["updated_at"])
    reasons = []
    if created >= since:
        reasons.append("opened in last 24h")
    if updated >= since:
        reasons.append("updated in last 24h")
    if labels & PRIORITY_LABELS:
        reasons.append("priority/bug/wrong-base label")
    if labels & WATCH_LABELS:
        reasons.append("watch label")
    if (pr.get("base") or {}).get("ref") != DEFAULT_BRANCH:
        reasons.append(f"base is `{(pr.get('base') or {}).get('ref')}`, not `{DEFAULT_BRANCH}`")
    if pr.get("draft"):
        reasons.append("draft")
    return reasons


def issue_reasons(issue: dict, since: datetime) -> list[str]:
    labels = label_names(issue)
    created = parse_ts(issue["created_at"])
    updated = parse_ts(issue["updated_at"])
    reasons = []
    if created >= since:
        reasons.append("opened in last 24h")
    if updated >= since:
        reasons.append("updated in last 24h")
    if labels & PRIORITY_LABELS:
        reasons.append("priority/bug label")
    if labels & WATCH_LABELS:
        reasons.append("watch label")
    return reasons


def main() -> None:
    rate_start = rate_limit_snapshot()
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)

    pulls = gh_api(f"repos/{OWNER_REPO}/pulls?state=open&sort=updated&direction=desc&per_page=100")[:MAX_ITEMS]
    issues = gh_api(f"repos/{OWNER_REPO}/issues?state=open&sort=updated&direction=desc&per_page=100")[:MAX_ITEMS]
    issues = [item for item in issues if "pull_request" not in item]

    pr_candidates = []
    stale_prs = []
    for pr in pulls:
        if pr.get("user", {}).get("login") == REVIEWER:
            continue
        reasons = pr_reasons(pr, since)
        if not reasons:
            continue
        item = {
            "number": pr["number"],
            "title": pr["title"],
            "url": pr["html_url"],
            "author": pr.get("user", {}).get("login"),
            "created_at": pr["created_at"],
            "updated_at": pr["updated_at"],
            "head_sha": pr["head"]["sha"],
            "base": (pr.get("base") or {}).get("ref"),
            "labels": sorted(label_names(pr)),
            "draft": bool(pr.get("draft")),
            "reasons": reasons,
        }
        if pr.get("draft"):
            stale_prs.append(item)
        else:
            pr_candidates.append(item)

    issue_candidates = []
    for issue in issues:
        if not is_interesting_issue(issue, since):
            continue
        issue_candidates.append(
            {
                "number": issue["number"],
                "title": issue["title"],
                "url": issue["html_url"],
                "author": issue.get("user", {}).get("login"),
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "labels": sorted(label_names(issue)),
                "reasons": issue_reasons(issue, since),
            }
        )

    rate_end = rate_limit_snapshot()
    core_remaining = rate_end.get("core_remaining")
    deep_budget_enabled = core_remaining is None or core_remaining >= MIN_CORE_RATE_REMAINING_FOR_DEEP_REVIEW
    deep_prs = pr_candidates[:MAX_HEAVY_PR_INSPECTIONS] if deep_budget_enabled else []
    overflow_prs = pr_candidates[len(deep_prs):]
    issue_triage = issue_candidates[:MAX_ISSUE_TRIAGE_INSPECTIONS] if deep_budget_enabled else []
    overflow_issues = issue_candidates[len(issue_triage):]

    print("# Daily RTK pilot sweep candidates")
    print()
    print(f"- Repository: `{OWNER_REPO}`")
    print(f"- Generated UTC: `{now.isoformat(timespec='seconds')}`")
    print(f"- Window start UTC: `{since.isoformat(timespec='seconds')}`")
    print(f"- Default branch: `{DEFAULT_BRANCH}`")
    print(f"- Watcher: `@{REVIEWER}`")
    print(f"- PR candidates found: `{len(pr_candidates)}`")
    print(f"- Issue candidates found: `{len(issue_candidates)}`")
    print(f"- Draft PRs skipped from deep review: `{len(stale_prs)}`")
    print(f"- GitHub core rate limit before script: `{rate_start.get('core_remaining')}/{rate_start.get('core_limit')}` remaining")
    print(f"- GitHub core rate limit after script: `{rate_end.get('core_remaining')}/{rate_end.get('core_limit')}` remaining")
    print(f"- Script GitHub API subprocess calls: `{_GH_API_CALLS}`")
    print()

    print("# Review budget for the agent")
    print()
    print(
        f"- Heavy PR inspections allowed this run: `{len(deep_prs)}/{MAX_HEAVY_PR_INSPECTIONS}` "
        f"(disable deep review below `{MIN_CORE_RATE_REMAINING_FOR_DEEP_REVIEW}` core requests remaining)"
    )
    print(f"- Issue triage inspections allowed this run: `{len(issue_triage)}/{MAX_ISSUE_TRIAGE_INSPECTIONS}`")
    print(f"- Max `gh pr diff` calls: `{MAX_DIFF_FETCHES}`")
    print(f"- Max comment/review-comment fetches combined: `{MAX_COMMENT_FETCHES}`")
    print("- Do not post GitHub comments; produce a Telegram brief with suggested watch/review targets only.")
    print("- Prefer shallow metadata/checks for overflow; Máté can request an explicit deep review later.")
    if not deep_budget_enabled:
        print("- Deep review disabled because the remaining core GitHub rate-limit budget is low.")
    print()

    print("# Deep-review PR candidates within this run's budget")
    print()
    if not deep_prs:
        print("No deep-review PR candidates within budget for this sweep.")
    for pr in deep_prs:
        print(f"- #{pr['number']} — {pr['title']} ({pr['url']})")
    if overflow_prs:
        print()
        print("# Overflow PR candidates for lightweight triage only")
        print()
        for pr in overflow_prs:
            print(f"- #{pr['number']} — {pr['title']} ({pr['url']})")

    print()
    print("# Issue triage candidates within this run's budget")
    print()
    if not issue_triage:
        print("No issue triage candidates within budget for this sweep.")
    for issue in issue_triage:
        print(f"- #{issue['number']} — {issue['title']} ({issue['url']})")
    if overflow_issues:
        print()
        print("# Overflow issues for lightweight trend watch only")
        print()
        for issue in overflow_issues:
            print(f"- #{issue['number']} — {issue['title']} ({issue['url']})")

    print()
    print("# PR candidate details")
    print()
    if not pr_candidates:
        print("No PR candidates found for this sweep.")
    for pr in pr_candidates:
        print(
            f"- #{pr['number']} — {pr['title']} ({pr['url']})\n"
            f"  - author: @{pr['author']}\n"
            f"  - reasons: {', '.join(pr['reasons'])}\n"
            f"  - labels: {', '.join(pr['labels']) or '(none)'}\n"
            f"  - base: `{pr['base']}`\n"
            f"  - updated: {pr['updated_at']}\n"
            f"  - head: `{pr['head_sha']}`"
        )

    print()
    print("# Issue candidate details")
    print()
    if not issue_candidates:
        print("No issue candidates found for this sweep.")
    for issue in issue_candidates:
        print(
            f"- #{issue['number']} — {issue['title']} ({issue['url']})\n"
            f"  - author: @{issue['author']}\n"
            f"  - reasons: {', '.join(issue['reasons'])}\n"
            f"  - labels: {', '.join(issue['labels']) or '(none)'}\n"
            f"  - updated: {issue['updated_at']}"
        )

    print()
    print("# Draft/skipped PRs")
    print()
    if not stale_prs:
        print("No draft PRs were skipped.")
    for pr in stale_prs:
        print(f"- #{pr['number']} — {pr['title']} ({pr['url']})")

    print()
    print("# RTK local review notes")
    print()
    print(f"- Repo clone/workdir: `/home/hermes/work/oss/rtk`")
    print("- Before local code review, run `pwd` and `git branch` per this repo's CLAUDE.md.")
    print("- Quality gate for code changes/review reproduction: `cargo fmt --all && cargo clippy --all-targets && cargo test --all`.")
    print("- Name collision: this is `rtk-ai/rtk` Rust Token Killer, not `reachingforthejack/rtk` Rust Type Kit.")
    if TODO_PATH.exists():
        print(f"- Existing pilot TODO note: `{TODO_PATH}`")


if __name__ == "__main__":
    main()
