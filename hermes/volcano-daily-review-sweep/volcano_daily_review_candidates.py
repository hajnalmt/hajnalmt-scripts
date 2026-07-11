#!/usr/bin/env python3
"""Collect Volcano PR review candidates for the daily Hermes review sweep."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

OWNER_REPO = "volcano-sh/volcano"
REVIEWER = "hajnalmt"
MAX_PRS = 100
TODO_PATH = Path("/home/hermes/work/private/notes/todos/volcano-maintainer.md")
MAX_HEAVY_PR_INSPECTIONS = 5
MAX_DIFF_FETCHES = 3
MAX_REVIEW_COMMENT_FETCHES = 5
MIN_CORE_RATE_REMAINING_FOR_DEEP_REVIEW = 1000


APPROVAL_META_RE = re.compile(r"<!-- META=(\{.*?\}) -->", re.DOTALL)
CHERRYPICK_RE = re.compile(r"^/cherrypick\s+(release-\d+\.\d+)\s*$", re.MULTILINE)
CREATED_PR_RE = re.compile(r"new pull request created:\s*#(\d+)", re.IGNORECASE)
TODO_WAITING_RE = re.compile(
    r"^- \[ \] #(\d+) — .*?latest PR update is (\d{4}-\d{2}-\d{2})",
    re.MULTILINE,
)

_REVIEWS_CACHE: dict[int, list[dict]] = {}
_GH_API_CALLS = 0


def gh_json(args: list[str], *, optional: bool = False):
    global _GH_API_CALLS
    last_error = None
    for attempt in range(2):
        try:
            _GH_API_CALLS += 1
            out = subprocess.check_output(
                ["gh", *args],
                text=True,
                stderr=subprocess.PIPE,
            )
            break
        except subprocess.CalledProcessError as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(2)
                continue
    else:
        if optional:
            print(
                f"Warning: failed optional gh {' '.join(args)} request: {last_error}",
                file=sys.stderr,
            )
            return []
        raise last_error
    return out


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


def gh_api(path: str, *, optional: bool = False):
    out = gh_json(["api", path, "--paginate"], optional=optional)
    if not out:
        return []
    chunks = []
    decoder = json.JSONDecoder()
    s = out.strip()
    while s:
        obj, idx = decoder.raw_decode(s)
        chunks.append(obj)
        s = s[idx:].strip()
    if not chunks:
        return []
    if len(chunks) == 1:
        return chunks[0]
    merged = []
    for chunk in chunks:
        if isinstance(chunk, list):
            merged.extend(chunk)
        else:
            merged.append(chunk)
    return merged


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_day_end(value: str) -> datetime:
    day = datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    return day + timedelta(days=1)


def existing_author_waiting_prs() -> dict[int, datetime]:
    """Return PRs already tracked as waiting on the author in the TODO.

    The daily sweep uses this as a cheap metadata-first gate: if a PR is
    already in the author-waiting bucket and GitHub's lightweight `updated_at`
    has not moved past the recorded date, do not fetch expensive comments,
    review comments, files, or diffs for it.
    """
    if not TODO_PATH.exists():
        return {}
    text = TODO_PATH.read_text(encoding="utf-8")
    return {int(number): parse_day_end(day) for number, day in TODO_WAITING_RE.findall(text)}


def user_reviews_after_head(pr_number: int, head_sha: str) -> list[dict]:
    if pr_number not in _REVIEWS_CACHE:
        _REVIEWS_CACHE[pr_number] = gh_api(f"repos/{OWNER_REPO}/pulls/{pr_number}/reviews")
    reviews = _REVIEWS_CACHE[pr_number]
    current = []
    for review in reviews:
        if review.get("user", {}).get("login") != REVIEWER:
            continue
        # A review on the current head SHA means this revision is already reviewed.
        if review.get("commit_id") == head_sha:
            current.append(review)
    return current


def has_user_review_after_head(pr_number: int, head_sha: str) -> bool:
    return bool(user_reviews_after_head(pr_number, head_sha))


def has_user_comment_review_after_head(pr_number: int, head_sha: str) -> bool:
    return any(
        (review.get("state") or "").upper() == "COMMENTED"
        for review in user_reviews_after_head(pr_number, head_sha)
    )


def latest_user_review_time_after_head(pr_number: int, head_sha: str) -> datetime | None:
    latest = None
    for review in user_reviews_after_head(pr_number, head_sha):
        submitted_at = review.get("submitted_at")
        if not submitted_at:
            continue
        ts = parse_ts(submitted_at)
        if latest is None or ts > latest:
            latest = ts
    return latest


def user_requested(pr: dict) -> bool:
    users = pr.get("requested_reviewers") or []
    teams = pr.get("requested_teams") or []
    return any(u.get("login") == REVIEWER for u in users) or any(
        t.get("slug") in {"volcano-maintainers", "maintainers"} for t in teams
    )


def label_names(pr: dict) -> set[str]:
    return {label.get("name", "") for label in pr.get("labels") or []}


def latest_approval_notifier_mentions_reviewer(pr_number: int) -> bool:
    """Return true if the latest approval-notifier comment names REVIEWER.

    Prow's approval-notifier does not necessarily request a GitHub review from
    the approver. It leaves an issue comment with hidden META like:
    <!-- META={"approvers":["hajnalmt"]} -->

    Include such PRs even when the current head was already reviewed, because
    the next action may be just `/approve`.
    """
    comments = gh_api(f"repos/{OWNER_REPO}/issues/{pr_number}/comments?per_page=100", optional=True)
    for comment in reversed(comments):
        if comment.get("user", {}).get("login") != "volcano-sh-bot":
            continue
        body = comment.get("body") or ""
        if "[APPROVALNOTIFIER]" not in body:
            continue
        for match in APPROVAL_META_RE.finditer(body):
            try:
                meta = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            if REVIEWER in set(meta.get("approvers") or []):
                return True
        # Fallback for notifier text if the META format changes.
        if f"from {REVIEWER}" in body or f"approval from {REVIEWER}" in body:
            return True
        return False
    return False


def needs_reviewer_followup(pr: dict) -> bool:
    labels = label_names(pr)
    if "approved" in labels:
        return False
    return latest_approval_notifier_mentions_reviewer(pr["number"])


def pr_summary(pr_number: int) -> dict | None:
    pr = gh_api(f"repos/{OWNER_REPO}/pulls/{pr_number}", optional=True)
    if not isinstance(pr, dict) or not pr:
        return None
    labels = [label.get("name", "") for label in pr.get("labels") or []]
    return {
        "number": pr_number,
        "title": pr.get("title"),
        "url": pr.get("html_url"),
        "state": pr.get("state"),
        "merged": bool(pr.get("merged_at")),
        "merged_at": pr.get("merged_at"),
        "base": (pr.get("base") or {}).get("ref"),
        "labels": sorted(labels),
    }


def recent_cherrypick_status(now: datetime) -> list[dict]:
    """Return recently merged source PRs where Prow cherrypicks were requested.

    This gives the agent a live validation section so it does not recommend
    already-completed backport work from stale review notes.
    """
    since = now - timedelta(days=14)
    pulls = gh_api(
        f"repos/{OWNER_REPO}/pulls?state=closed&sort=updated&direction=desc&per_page=100",
        optional=True,
    )[:MAX_PRS]
    status = []
    for pr in pulls:
        merged_at = pr.get("merged_at")
        if not merged_at or parse_ts(merged_at) < since:
            continue
        comments = gh_api(
            f"repos/{OWNER_REPO}/issues/{pr['number']}/comments?per_page=100",
            optional=True,
        )
        requested = []
        created = []
        for comment in comments:
            body = comment.get("body") or ""
            for target in CHERRYPICK_RE.findall(body):
                requested.append(
                    {
                        "target": target,
                        "by": comment.get("user", {}).get("login"),
                        "created_at": comment.get("created_at"),
                        "url": comment.get("html_url"),
                    }
                )
            if comment.get("user", {}).get("login") == "volcano-sh-bot":
                for created_pr in CREATED_PR_RE.findall(body):
                    summary = pr_summary(int(created_pr))
                    if summary:
                        created.append(summary)
        if requested or created:
            status.append(
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "url": pr["html_url"],
                    "merged_at": merged_at,
                    "requested": requested,
                    "created": created,
                }
            )
    return status


def main() -> None:
    rate_start = rate_limit_snapshot()
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)
    pulls = gh_api(
        f"repos/{OWNER_REPO}/pulls?state=open&sort=updated&direction=desc&per_page=100"
    )[:MAX_PRS]

    candidates = []
    author_waiting = []
    metadata_skipped_author_waiting = []
    known_author_waiting = existing_author_waiting_prs()
    for pr in pulls:
        created = parse_ts(pr["created_at"])
        updated = parse_ts(pr["updated_at"])
        head_sha = pr["head"]["sha"]
        labels = label_names(pr)
        if pr.get("draft"):
            continue
        if pr.get("user", {}).get("login") == REVIEWER:
            continue
        waiting_until = known_author_waiting.get(pr["number"])
        if waiting_until and updated <= waiting_until:
            metadata_skipped_author_waiting.append(
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "url": pr["html_url"],
                    "author": pr.get("user", {}).get("login"),
                    "updated_at": pr["updated_at"],
                    "labels": sorted(labels),
                    "reason": "already in TODO author-waiting bucket and lightweight updated_at has not moved",
                }
            )
            continue
        requested = user_requested(pr)
        approval_needed = needs_reviewer_followup(pr)
        opened_last_24h = created >= since
        updated_last_24h = updated >= since
        # Keep the daily list focused: new PRs from the last 24h, PRs
        # explicitly waiting on Hajnal's review, PRs where Prow says
        # @hajnalmt is the needed approver, plus recently updated PRs where
        # Hajnal may already have left a COMMENTED review on the current head
        # but no `lgtm` label is present. Avoid fetching review history for
        # old, unrequested, no-approval PRs; those can be deep-reviewed on
        # explicit request without burning the daily quota.
        if not (opened_last_24h or requested or approval_needed or updated_last_24h):
            continue
        already_reviewed_head = has_user_review_after_head(pr["number"], head_sha)
        commented_review_head = has_user_comment_review_after_head(pr["number"], head_sha)
        latest_hajnal_review = latest_user_review_time_after_head(pr["number"], head_sha)
        needs_comment_followup = commented_review_head and "lgtm" not in labels
        waiting_on_author_after_feedback = (
            needs_comment_followup
            and latest_hajnal_review is not None
            and updated <= latest_hajnal_review + timedelta(minutes=5)
        )
        if waiting_on_author_after_feedback:
            author_waiting.append(
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "url": pr["html_url"],
                    "author": pr.get("user", {}).get("login"),
                    "updated_at": pr["updated_at"],
                    "head_sha": head_sha,
                    "latest_hajnal_review": latest_hajnal_review.isoformat(timespec="seconds"),
                    "labels": sorted(labels),
                    "reason": "@hajnalmt already left current-head feedback and the PR has not moved since",
                }
            )
            continue
        if not (opened_last_24h or requested or approval_needed or needs_comment_followup):
            continue
        if already_reviewed_head and not (approval_needed or needs_comment_followup):
            continue
        candidates.append(
            {
                "number": pr["number"],
                "title": pr["title"],
                "url": pr["html_url"],
                "author": pr.get("user", {}).get("login"),
                "created_at": pr["created_at"],
                "updated_at": pr["updated_at"],
                "head_sha": head_sha,
                "requested": requested,
                "approval_needed": approval_needed,
                "already_reviewed_head": already_reviewed_head,
                "commented_review_head": commented_review_head,
                "needs_comment_followup": needs_comment_followup,
                "opened_last_24h": opened_last_24h,
                "updated_last_24h": updated_last_24h,
                "labels": sorted(labels),
            }
        )

    rate_end = rate_limit_snapshot()
    core_remaining = rate_end.get("core_remaining")
    deep_budget_enabled = (
        core_remaining is None
        or core_remaining >= MIN_CORE_RATE_REMAINING_FOR_DEEP_REVIEW
    )
    deep_candidates = candidates[:MAX_HEAVY_PR_INSPECTIONS] if deep_budget_enabled else []
    overflow_candidates = candidates[len(deep_candidates):]

    print("# Daily Volcano PR review candidates")
    print()
    print(f"- Repository: `{OWNER_REPO}`")
    print(f"- Generated UTC: `{now.isoformat(timespec='seconds')}`")
    print(f"- Window start UTC: `{since.isoformat(timespec='seconds')}`")
    print(f"- Reviewer: `@{REVIEWER}`")
    print(f"- Candidates found: `{len(candidates)}`")
    print(f"- Moved/kept author-waiting without full review: `{len(author_waiting) + len(metadata_skipped_author_waiting)}`")
    print(f"- GitHub core rate limit before script: `{rate_start.get('core_remaining')}/{rate_start.get('core_limit')}` remaining")
    print(f"- GitHub core rate limit after script: `{rate_end.get('core_remaining')}/{rate_end.get('core_limit')}` remaining")
    print(f"- Script GitHub API subprocess calls: `{_GH_API_CALLS}`")
    print()

    print("# Review budget for the agent")
    print()
    print(
        f"- Heavy PR inspections allowed this run: `{len(deep_candidates)}/{MAX_HEAVY_PR_INSPECTIONS}` "
        f"(disable deep review below `{MIN_CORE_RATE_REMAINING_FOR_DEEP_REVIEW}` core requests remaining)"
    )
    print(f"- Max `gh pr diff` calls: `{MAX_DIFF_FETCHES}`")
    print(f"- Max review-comment fetches: `{MAX_REVIEW_COMMENT_FETCHES}`")
    print(
        "- Use metadata/checks/TODO updates for overflow candidates; Máté can request an explicit deep review for any PR later."
    )
    if not deep_budget_enabled:
        print("- Deep review disabled because the remaining core GitHub rate-limit budget is low.")
    print()

    print("# Deep-review candidates within this run's budget")
    print()
    if not deep_candidates:
        print("No deep-review candidates within budget for this sweep.")
    for pr in deep_candidates:
        print(f"- #{pr['number']} — {pr['title']} ({pr['url']})")
    if overflow_candidates:
        print()
        print("# Overflow candidates for lightweight triage only")
        print()
        for pr in overflow_candidates:
            print(f"- #{pr['number']} — {pr['title']} ({pr['url']})")
    print()
    print("# Candidate details")
    print()
    if not candidates:
        print("No candidate PRs found for this sweep.")
    for pr in candidates:
        reasons = []
        if pr["approval_needed"]:
            reasons.append("Prow says @hajnalmt approval/follow-up needed")
        if pr["requested"]:
            reasons.append("review requested")
        if pr["opened_last_24h"]:
            reasons.append("opened in last 24h")
        if pr["updated_last_24h"]:
            reasons.append("updated in last 24h")
        if pr["already_reviewed_head"]:
            reasons.append("current head already reviewed by @hajnalmt")
        if pr["needs_comment_followup"]:
            reasons.append("@hajnalmt left COMMENTED review; no lgtm label yet — preserve linewise follow-up")
        print(
            f"- #{pr['number']} — {pr['title']} ({pr['url']})\n"
            f"  - author: @{pr['author']}\n"
            f"  - reasons: {', '.join(reasons)}\n"
            f"  - labels: {', '.join(pr['labels']) or '(none)'}\n"
            f"  - updated: {pr['updated_at']}\n"
            f"  - head: `{pr['head_sha']}`"
        )

    print()
    print("# Author-waiting / no-current-action PRs")
    print()
    print(
        "Move these to the TODO section `Waiting on author after Máté feedback — "
        "no current Máté action` or leave them there. Do not fetch diffs/files "
        "or prepare review notes unless `updated_at` moves after Máté's latest "
        "recorded feedback."
    )
    print()
    if not author_waiting and not metadata_skipped_author_waiting:
        print("No PRs classified as author-waiting by the lightweight gate.")
    for pr in author_waiting:
        print(
            f"- #{pr['number']} — {pr['title']} ({pr['url']})\n"
            f"  - author: @{pr['author']}\n"
            f"  - reason: {pr['reason']}\n"
            f"  - labels: {', '.join(pr['labels']) or '(none)'}\n"
            f"  - latest Hajnal review: {pr['latest_hajnal_review']}\n"
            f"  - updated: {pr['updated_at']}\n"
            f"  - head: `{pr['head_sha']}`"
        )
    for pr in metadata_skipped_author_waiting:
        print(
            f"- #{pr['number']} — {pr['title']} ({pr['url']})\n"
            f"  - author: @{pr['author']}\n"
            f"  - reason: {pr['reason']}\n"
            f"  - labels: {', '.join(pr['labels']) or '(none)'}\n"
            f"  - updated: {pr['updated_at']}"
        )

    backports = recent_cherrypick_status(now)
    print()
    print("# Recent Prow cherrypick/backport status")
    print()
    print(
        "Use this live section to validate stale review-note TODOs before "
        "recommending more `/cherrypick` commands."
    )
    print()
    if not backports:
        print("No recent merged PRs with Prow cherrypick activity found.")
        return
    for item in backports:
        print(f"- Source #{item['number']} — {item['title']} ({item['url']})")
        print(f"  - merged: {item['merged_at']}")
        if item["requested"]:
            requested = ", ".join(
                f"{r['target']} by @{r['by']}" for r in item["requested"]
            )
            print(f"  - requested: {requested}")
        if item["created"]:
            print("  - created PRs:")
            for child in item["created"]:
                merged = "merged" if child["merged"] else child["state"]
                print(
                    f"    - #{child['number']} ({child['base']}): {merged}; "
                    f"labels: {', '.join(child['labels']) or '(none)'}; {child['url']}"
                )


if __name__ == "__main__":
    main()
