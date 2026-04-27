---
sidebar_position: 2
---

# AI-Assisted Workflow

During the development lifecycle of this experimental prototype, Large Language Models (LLMs) were utilized as engineering aids. This document outlines how AI tools were integrated into the standard development workflow.

## Applications of AI Assistance

1. **Rapid Prototyping (Boilerplate Generation):**
   AI models were used to generate standard boilerplate code, particularly for the FastAPI web server routing and the React/Docusaurus frontend configurations. This accelerated initial setup.

2. **Hardware Interfacing Guidance:**
   LLMs provided reference implementations for the C++ MFRC522 SPI library and Keypad matrix scanning, which were subsequently refined and adapted to the specific pinout of the prototype.

3. **Documentation Structuring:**
   AI tools assisted in formatting raw engineering notes into structured markdown documents and generating Mermaid diagram syntax based on natural language descriptions of the architecture.

## Workflow Integration Guidelines

To maintain code quality and security, the following guidelines were strictly adhered to:
- **Zero-Trust Review:** All AI-generated code was subjected to manual code review and local unit testing.
- **Architectural Authority:** Core architectural decisions (e.g., synchronous vs asynchronous processing, database schema design) were made by human engineers; AI was strictly used for implementation execution.
- **Security Primitives:** Cryptographic operations (e.g., PIN hashing via `bcrypt`) were manually verified against industry best practices rather than relying solely on AI suggestions.
