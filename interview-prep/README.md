# Interview preparation gym

A small, repeatable practice project for rebuilding live-coding muscle memory without turning it into random LeetCode suffering.

The goal is not to prove engineering worth with fabricated puzzles. The goal is to build enough interview fluency that small coding tasks do not falsely filter out strong senior/MLOps/platform skills.

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
- small structs
- explicit error handling

## Weekly pressure practice

Once per week, solve one previous problem in 30 minutes while speaking aloud.

This is not because live-coding interviews are good. It is nervous-system exposure: training the body not to interpret a small implementation task as danger.

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

## Why this exists

AI can generate small functions quickly. The useful human skill is still being able to:

- define the required behavior precisely,
- notice missing edge cases,
- evaluate generated code,
- write tests,
- debug failures,
- and pass outdated interview gates when necessary.

This project is anti-humiliation armor, not an endorsement of bad interviews.
