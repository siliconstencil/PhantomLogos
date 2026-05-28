---
name: design-suite
description: UI/UX design workflow - consultation, rapid prototyping, HTML generation, and design review with vision pipeline support.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
  - vision
  - write_file
  - replace_content
  - semantic
  - mcp_slm_remember
  - mcp_slm_recall
  - ls
tier: 2
when_to_use:
  - User requests new UI design or page layout.
  - Visual mockup analysis or design critique.
  - Rapid HTML/CSS prototyping.
  - Design consultation on UX patterns and accessibility.
metadata:
  audience: developers
  tier: L2-Runner
  workflow: design
---

# Skill: Design Suite

Comprehensive UI/UX design workflow covering the full design lifecycle: consultation -> rapid prototyping (shotgun) -> HTML generation -> design review. Integrates with the vision pipeline (Qwen2.5-VL) for mockup analysis and the code-generation skill for production-ready output.

## Workflow

1.  **Consultation (design-consultation):** Gather requirements: target audience, brand guidelines, accessibility needs, device targets. Use vision pipeline to analyze any reference images. Produce a design brief with constraints.

2.  **Rapid Prototyping (design-shotgun):** Generate 2-3 divergent visual concepts using the vision model or Tailwind-based HTML mockups. Present options with trade-offs. Let the user select or guide direction.

3.  **HTML Generation (design-html):** Convert the selected concept into production-ready HTML/CSS. Follow existing component patterns from the codebase (use ui-design-premium conventions). Ensure responsive layout, dark/light mode support, and BA-01 compliance.

4.  **Design Review (design-review):** Run a structured design audit: accessibility (WCAG 2.1 AA), visual consistency, responsive breakpoints, performance (image optimization, bundle size). Use vision analysis for visual regression against the mockup.

## Guardrails
- NEVER use placeholder images in production output; use actual asset paths.
- ALWAYS validate HTML output with verify before finalizing.
- Respect EMOJI_BAN: no emoji in UI text.
- For existing projects, use semantic search (Axis 6) to match design system conventions before generating new components.
- Color contrast must meet WCAG 2.1 AA minimum (4.5:1 for normal text).

## Output Format
- `design_brief`: Requirements, constraints, and reference analysis.
- `prototypes`: 2-3 concept variants with rationale.
- `html_output`: Production-ready HTML/CSS with responsive breakpoints.
- `review_report`: Accessibility score, visual consistency score, action items.
