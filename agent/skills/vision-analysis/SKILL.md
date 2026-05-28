---
name: vision-analysis
description: Analyzing UI mockups, diagrams, and visual assets via multimodal models.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
- vision
- write_file
- semantic
- mcp_slm_remember
tier: 2
---
# Skill: Vision Analysis
Bridges the gap between visual intent and technical implementation.

## Axis 14 Standards
Every visual task is governed by Mnemosyne Axis 14 for long-term memory and L3 audit for fidelity.

### Multimodal Pipeline
1. **Optimization**: Images are processed via `ImageOptimizer` to fix EXIF and normalize resolution (max 1024px).
2. **Task-Aware Routing**:
   - **OCR Mode**: Precise text extraction.
   - **Thinking Mode**: Structural and logical analysis of diagrams/circuits.
   - **Creative Mode**: High-fidelity scene and style description.
3. **Memory Integration**: Descriptions are indexed via **Nomic Embed** for cross-session retrieval.

### Adversarial Audit (Lachesis)
Vision outputs are scored on:
- **OCR Accuracy**: Literal text match against VLM output.
- **Visual Consistency**: Alignment with historical Axis 14 memories.
- **Hallucination Check**: Cross-referencing detected objects with task requirements.

## Best Practices
- Always mention [SRC:axis_14] when referencing visual data.
- For UI tasks, prefer `Thinking Mode` to understand layout logic before coding.
- Use `OCR Mode` for error logs and documentation screenshots.
