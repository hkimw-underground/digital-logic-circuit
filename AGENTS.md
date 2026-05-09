# AGENTS.md

This repository is a school capstone project for a 2FA smart door lock system.

Use Jules as an AI coding agent to help with documentation, report cleanup, translation, diagrams, website docs, and small implementation tasks when the issue asks for them. Jules is not a human contributor, and the maintainer still decides what to merge.

## Default workflow

Use this simple workflow:

```text
Issue → Jules task → Pull request → Review → Merge
```

For this repository, documentation and report-polish work can be handled more freely than production software work. The goal is to improve the project presentation and leave a useful GitHub history.

## Repository context

This project is a smart door lock system built around:

- digital logic circuit capstone work
- NFC/PIN first-factor authentication
- YOLO-based face recognition as a second factor
- Raspberry Pi and hardware integration
- a Docusaurus report website

## Rules for Jules

- Treat the linked GitHub Issue as the source of truth.
- Prefer clear, natural school-report writing over AI-sounding wording.
- Documentation, translation, README, website docs, and report cleanup may be edited boldly when the issue asks for it.
- Keep public-facing writing practical and human-written.
- Avoid hype, emojis, exaggerated claims, and “AI did everything” language.
- Keep PRs reviewable, but do not be overly timid on documentation improvements.
- Include a short validation note in every PR.
- Do not add secrets, credentials, tokens, private paths, or generated bulky artifacts.
- Do not self-merge.

## Code and hardware changes

Code and hardware changes are allowed when an issue explicitly asks for them, but the PR should explain what changed and how it was checked.

Use extra care for:

- lock or unlock behavior
- NFC authentication
- PIN authentication
- face recognition and model loading
- camera failure handling
- database records
- GPIO, relay, servo, or physical hardware control

For documentation-only changes, do not over-emphasize safety boundaries. Keep the writing focused on the school project, system design, usage, validation, and report quality.

## Validation expectations

For documentation-only changes, check Markdown readability, links, and Docusaurus build when relevant.

For code changes, include tests, command output, manual checks, or a note explaining what requires the physical setup.

## Case Study note

This repository can be used as a practical example of Jules-assisted development, but the repository itself should continue to read primarily as a school capstone project.
