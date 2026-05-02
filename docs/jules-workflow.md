# Jules Workflow for Digital Logic Circuit

This repository uses Jules as an AI coding agent inside a human-maintained GitHub workflow.

The project is a real hardware/software capstone project. Changes can affect authentication, hardware control, fail-safe behavior, and deployment assumptions. Human review is required before merge.

## Default workflow

Use this Review-Driven workflow by default:

```text
Issue → Jules task → Pull request → CI → Human review → Merge
```

## Repository roles

| Role | Responsibility |
| --- | --- |
| Human maintainer | Scope, architecture, hardware judgment, security decisions, validation, review, and merge decisions. |
| Jules | Scoped implementation or documentation assistance through issues and pull requests. |
| CI | Lightweight checks for documentation, YAML syntax, and starter workflow file presence. |

Jules is not a human contributor. Jules-assisted work must remain reviewable by the human maintainer.

## What Jules can help with

Good Jules tasks include:

- documentation cleanup
- validation log formatting
- issue and PR template maintenance
- small testable utility changes
- CI maintenance
- refactoring only when the issue gives clear scope and validation requirements

## What requires extra care

The maintainer must inspect changes involving:

- NFC authentication
- PIN authentication
- face recognition
- YOLO model loading
- camera failure handling
- Raspberry Pi GPIO behavior
- lock, relay, servo, or actuator control
- fail-safe behavior
- database records for users or authentication state
- deployment instructions for real hardware

If a task touches these areas, the issue and PR must explain the risk and validation plan.

## First setup workflow

The first Jules workflow setup should only add repository operation files:

- `AGENTS.md`
- `.github/ISSUE_TEMPLATE/jules_task.yml`
- `.github/ISSUE_TEMPLATE/workflow_experiment.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/docs-and-templates.yml`
- `docs/jules-workflow.md`

It should not change application behavior.

## Issue quality checklist

A good issue for Jules should include:

- Goal
- Context
- Scope
- Non-goals
- Risk areas
- Acceptance Criteria
- Validation
- Output Required

The issue should make clear what Jules may change and what must not change.

## PR review checklist

Before merge, the maintainer should check:

- Does the PR match the linked issue?
- Is the diff small enough to review?
- Are unrelated refactors avoided?
- Are validation notes included?
- Did CI pass?
- Are hardware or security assumptions clear?
- Does the PR preserve fail-safe behavior?
- Is Jules framed as an AI coding agent rather than a human contributor?

## Validation notes

For documentation-only PRs:

- check Markdown readability
- check relative links
- check YAML syntax if templates changed

For code PRs:

- run available tests
- document manual checks
- explain any hardware-only validation that cannot be performed locally

For hardware-sensitive PRs:

- do not merge solely based on generated code
- inspect the behavior manually
- verify fail-safe assumptions
- record validation evidence when possible

## Connection to the starter kit

This repository is Case Study A for `hkimw-underground/vibe-coding-with-jules`.

Lessons from this repository should be generalized back into the starter kit only after they are proven through real issues, pull requests, CI checks, and human review.
