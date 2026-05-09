# Issue Proposal: [Jules] Add lightweight validation log template

## Goal
Create a lightweight validation log template for future Jules-assisted work to ensure readable and standardized validation history.

## Context
This project is a real capstone case study where Jules assists in development. High-risk areas (hardware, security, authentication) require explicit validation notes. The maintainer owns all hardware and merge decisions. A standardized log helps the maintainer review AI-generated changes effectively.

## Scope
This issue asks for a docs-only PR that adds a simple validation log template (e.g., `docs/validation_log_template.md`).

The template must include sections for:
- Task summary
- Linked issue
- PR link
- Validation performed (e.g., tests run, manual checks)
- Hardware/security notes (what was/wasn't verified on hardware)
- Maintainer review notes (specific areas for human inspection)
- Known limitations

## Non-goals
- Do not add any automation or scripts.
- Do not change CI workflows.
- Do not modify any application behavior or authentication logic.
- Do not claim validation was performed unless explicit evidence exists.

## Acceptance Criteria
- The output must be a Markdown template only.
- The template must clearly separate claimed validation from pending validation.
- The template must make the human maintainer responsibility explicit.
- The PR fulfilling this issue must include relative links and pass Markdown hygiene validation.

## Validation
- Confirm the issue was created in the project's tracking system.
- Confirm the requested task is docs-only.
