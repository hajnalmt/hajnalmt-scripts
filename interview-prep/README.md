# Interview preparation gym

A small, repeatable practice project for rebuilding live-coding muscle memory without turning it into random LeetCode suffering.

The goal is not to prove engineering worth with fabricated puzzles. The goal is to build enough interview fluency that small coding tasks do not falsely filter out strong senior/MLOps/platform skills.

This project is anti-humiliation armor, not an endorsement of bad interviews.

## Why this exists

Traditional live coding interviews often measure recent practice, syntax recall, stress tolerance, and familiarity with interview patterns more than senior engineering judgment. In an AI-assisted engineering world, the more valuable skills are problem framing, edge-case discovery, code review, validation, debugging, and integration.

AI can generate small functions quickly. The useful human skill is still being able to:

- define the required behavior precisely,
- notice missing edge cases,
- evaluate generated code,
- write tests,
- debug failures,
- and pass outdated interview gates when necessary.

Still, these tasks remain common hiring gates. The goal is not to become a LeetCode athlete. The goal is to build enough practical fluency that simple fabricated tasks do not unfairly block access to roles where deeper MLOps, platform, architecture, and review skills matter.

## Principles

- Practice practical interview-shaped tasks, not trivia.
- Solve the same problem in Python and Go.
- Optimize for repetition and retention, not the number of unique problems.
- Write edge cases before implementation.
- Use tests as the real feedback loop.
- Keep a mistake log so forgetting becomes part of the system, not a source of shame.
- Avoid adding Rust for now; Python and Go are the highest-return languages for this goal.

## Daily routine

Target time: 35-50 minutes.

1. Read the problem and write examples first.
   - Valid inputs
   - Invalid inputs
   - Edge cases
   - Assumptions
2. Attempt the Python solution from memory for 10-15 minutes.
   - No AI during the first attempt.
   - Cheat sheet or docs are allowed after the initial attempt.
3. Attempt the Go solution for 10-15 minutes.
   - Prefer idiomatic Go.
   - Use table-driven tests.
4. Run tests and fix issues.
5. Add a short note to the mistake log.

The goal is not memorizing every syntax detail. The goal is practicing the loop:

clarify -> examples -> edge cases -> implementation -> tests -> debug -> explanation

## Spaced repetition schedule

For each problem, redo it from scratch:

- Day 0: first solve
- Day 1: redo
- Day 7: redo
- Day 21: redo

Do not do 100 problems once. Do about 30 practical problems repeatedly until the patterns become boring.

## Suggested structure

```text
interview-prep/
  README.md
  cheatsheets/
    python.md
    go.md
  mistake-log.md
  postmortems/
    2026-07-10-arm-valid-number.md
  problems/
    001-valid-number/
      README.md
      python/
        solution.py
        test_solution.py
      go/
        go.mod
        solution.go
        solution_test.go
      notes.md
```

## Postmortems

- [Arm interview: valid number](postmortems/2026-07-10-arm-valid-number.md)

## Problem template

Each problem should answer these sections:

```markdown
# Problem: <name>

## Task

## Clarifications

## Examples

## Edge cases

## Python

## Go

## Complexity

## Mistakes / forgotten syntax

## Interview explanation
```

## First 10 tasks

1. Valid number parser
2. Key=value parser
3. Valid parentheses/brackets
4. First non-repeating character
5. Deduplicate records by ID, keeping the latest timestamp
6. Top-k frequent words or log messages
7. Merge overlapping intervals
8. Normalize Unix path
9. Parse duration strings like `1h30m20s`
10. Rate limiter per user

These are still artificial, but they are closer to practical infra/platform work than many abstract puzzle tasks.

## Interview muscle memory sequence

Use this sequence every time, even when the problem looks simple:

1. Clarify accepted input and output.
2. Write examples.
3. List edge cases.
4. Choose a simple approach.
5. Implement slowly.
6. Run tests or simulate them aloud.
7. Explain complexity and tradeoffs.

## Python survival patterns

Keep these close until they become automatic:

- `dict`, `set`, `list`
- `collections.Counter`
- `collections.defaultdict`
- `collections.deque`
- `heapq`
- `sorted(..., key=...)`
- `enumerate`, `zip`
- `str.strip`, `str.split`, `str.isdigit`
- `re.fullmatch`
- `try` / `except ValueError`

## Go survival patterns

Practice these in every Go solution:

- `make(map[string]int)`
- `append`
- `for _, v := range values`
- `strings.TrimSpace`, `strings.Split`, `strings.Fields`
- `strconv.Atoi`, `strconv.ParseFloat`
- `regexp.MustCompile`
- `sort.Slice`
- table-driven tests
- `t.Run`
- small structs
- explicit error returns

Every Go solution should have table-driven tests.

## Weekly pressure practice

Once per week, solve one previous problem in 30 minutes while speaking aloud.

This is not because live-coding interviews are good. It is nervous-system exposure: training the body not to interpret a small implementation task as danger.

Use this script:

1. Restate the problem.
2. Ask or write assumptions.
3. Give examples.
4. Implement the simplest correct version.
5. Test edge cases.
6. Explain complexity and tradeoffs.

## Suggested first problem: valid number

Implement `is_valid_number(s)` / `IsValidNumber(s string) bool`.

Start without regex. Use a manual parser or state-machine style first.

Test cases:

| Input | Expected |
| --- | --- |
| `"0"` | `true` |
| `" 0.1 "` | `true` |
| `"abc"` | `false` |
| `"1 a"` | `false` |
| `"2e10"` | `true` |
| `"-90E3"` | `true` |
| `"1e"` | `false` |
| `"e3"` | `false` |
| `"."` | `false` |
| `".1"` | `true` |
| `"1."` | `true` |
| `"+.8"` | `true` |
| `"46.e3"` | `true` |
| `"--6"` | `false` |
| `"-+3"` | `false` |
| `"95a54e53"` | `false` |

## Mistake log format

Example:

```text
2026-07-03 - valid number
Forgot Python: re.fullmatch exists.
Forgot Go: regexp.MatchString returns (bool, error), or use MustCompile.
Missed edge case: "." should be false.
Pattern: validation grammar with optional sign, decimal part, and exponent.
```

The mistake log is the most important artifact. It turns forgetting into training data instead of shame.

## Rust decision

Do not add Rust to this practice loop yet.

Rust is useful, but for job-switch readiness the highest-return path is Python plus Go plus interview composure. Rust can be added later after this loop is stable.

## Principle

This project does not concede that live coding interviews are a good senior-engineering evaluation method.

It exists because some companies still use them, and passing the gate preserves optionality.
