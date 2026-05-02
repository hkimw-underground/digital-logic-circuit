# AGENTS.md

This repository is a real hardware/software capstone project using a Jules-assisted GitHub workflow.

Jules is an AI coding agent. Jules is not a human contributor. The human maintainer owns hardware judgment, architecture, security decisions, validation, review, and merge decisions.

## Default workflow

Use the Review-Driven workflow by default:

```text
Issue → Jules task → Pull request → CI → Human review → Merge
```

Every Jules-assisted change should start from a GitHub Issue and end in a human-reviewed pull request.

## Repository context

This project is a smart door lock system built around:

- digital logic circuit capstone work
- NFC/PIN first-factor authentication
- YOLO-based face recognition as a second factor
- Raspberry Pi and hardware integration
- security-sensitive fail-safe behavior

The system should remain fail-safe. If hardware, camera, model loading, identity checks, or authentication state is uncertain, the safe behavior is to keep access blocked.

## Rules for Jules

- Treat the linked GitHub Issue as the source of truth.
- Keep pull requests small and focused.
- Do not change hardware behavior unless the issue explicitly asks for it.
- Do not modify authentication logic unless the issue explicitly asks for it.
- Do not weaken fail-safe behavior.
- Do not add secrets, private credentials, keys, tokens, or local machine paths.
- Do not perform opportunistic refactors.
- Do not rewrite large documents unless the issue explicitly asks for it.
- Include validation notes in every PR.
- Call out assumptions and areas that require human inspection.
- Do not self-merge.

## High-risk areas

Changes in these areas require careful human review:

- lock or unlock behavior
- NFC authentication
- PIN authentication
- face recognition and model loading
- camera availability and failure handling
- database access and identity records
- GPIO, relay, servo, or physical hardware control
- security analysis and threat assumptions
- deployment instructions that affect real hardware

## Validation expectations

A Jules-assisted PR should explain:

```text
What issue does this solve?
What changed?
What did not change?
How was it validated?
What assumptions were made?
What should the human maintainer inspect carefully?
```

For documentation-only changes, validate Markdown readability and links.

For code changes, include the relevant command output, tests, manual checks, or reason why local hardware validation is required.

For hardware-sensitive changes, state what cannot be verified without the physical setup.

## Case Study A note

This repository is intended to serve as Case Study A for `hkimw-underground/vibe-coding-with-jules`.

The goal is to leave a readable GitHub history of issues, Jules-assisted pull requests, CI checks, human review, and validation decisions.
