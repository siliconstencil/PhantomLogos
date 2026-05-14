---
name: prompt-compression
description: Compressing long prompts into high-density tokens via semantic distillation.
version: 1.0.0
license: MIT
compatibility: opencode
when_to_use:
  - Injecting massive 14-axis memory state into a single prompt.
  - Optimizing recursive reasoning loops.
metadata:
  audience: developers
  tier: Atropos
  workflow: optimization
---
# Skill: Prompt Compression (Sovereign Edition)

Maximizes the signal-to-noise ratio in model communications by distilling large context windows into high-density tokens without losing structural integrity.

## Workflow
1.  **Categorize**: Identify context blocks as `Volatile` (temporary), `Structural` (code/schema), or `Rational` (facts).
2.  **Select Mode**:
    - **Lossless**: Use for code, schemas, and governance rules (Standard minification).
    - **Lossy**: Use for long conversation histories or descriptive logs (Semantic distillation).
3.  **Distill**: Remove redundant adjectives, repetitive meta-talk, and boilerplate while preserving key entities and relationships.
4.  **Verify**: Perform a quick similarity check (Axis 6) to ensure the compressed version maintains the semantic meaning of the original.
5.  **Inject**: Insert the compressed state into the reasoning context using the `[COMPRESSED]` tag.

## Guardrails
- **Critical Keys**: Never compress file paths, API keys, or unique identifiers (UUIDs).
- **Token Budget**: Compression should only be triggered when the total prompt size exceeds 70% of the active model's context window.
- **Integrity**: If a lossy compression drops the similarity score below 0.85, revert to the original or use a higher fidelity method.

## Output Format
- `compressed_prompt`: The high-density text output.
- `original_tokens`: Token count before compression.
- `final_tokens`: Token count after compression.
- `compression_ratio`: Percentage of tokens saved.
- `method_used`: Either `lossy` or `lossless`.
