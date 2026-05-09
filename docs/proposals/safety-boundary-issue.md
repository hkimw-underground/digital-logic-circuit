# Issue Proposal: Document AI-Assisted Coding Safety Boundaries

## Goal
Document the safety boundaries and operational scope for AI-assisted coding (Jules) within this smart door lock capstone project.

## Context
This project involves critical components such as NFC/PIN authentication, YOLO-based face recognition, and Raspberry Pi hardware integration. Given the security-sensitive nature of a smart door lock and the "Fail-Safe" principle of the system, it is essential to define clear boundaries for AI assistance. We must ensure that Jules remains a tool for human developers and never assumes ownership of security or hardware-critical decisions.

## Scope
Create a docs-only Pull Request (PR) that updates the project documentation (e.g., `AGENTS.md` and `docs/jules-workflow.md`) to explicitly cover:

- **Assistance Scope:** Define what Jules can and cannot assist with (e.g., boilerplate, documentation, small utility functions vs. core security logic).
- **Human Review Requirements:** List specific areas where human review is mandatory and non-negotiable.
- **Hardware & Security Sensitivity:** Identify files and modules that are considered "high-risk" (e.g., `server/vision_ai.py`, `server/main.py` lock control, etc.).
- **Fail-Safe Behavior Ownership:** State clearly that the human maintainer is the sole owner of fail-safe logic and hardware behavior decisions.
- **Validation Expectations:** Define how AI-assisted changes must be validated, especially when they touch areas that cannot be tested without physical hardware.

## Non-goals
- Do not implement or modify any security logic.
- Do not modify authentication code.
- Do not change hardware behavior.
- Do not make security claims without empirical evidence or human verification.

## Risk
Low (Documentation only).

## Acceptance Criteria
- The documentation is clear, concise, and uses practical, non-hype language.
- The documentation avoids presenting Jules as a human contributor.
- The documentation explicitly lists hardware/security-sensitive areas.
- The PR requires review and approval from a human maintainer.

## Validation
- Confirm Markdown readability.
- Verify all relative links within the documentation.
- Ensure the guidance aligns with the "Fail-Safe" philosophy of the project.

## Output Required
A docs-only PR updating the relevant safety boundary documentation.
