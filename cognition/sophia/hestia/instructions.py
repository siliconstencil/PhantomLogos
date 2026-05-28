def get_sophia_instructions(tools: list[str]) -> dict:
    return {
        "tool": f"""
TOOL USAGE AND STRUCTURE GUIDELINES:
You MUST provide your response in valid JSON format matching this schema:
{{
  "thought": "your internal reasoning and citations [SRC:axis_N]",
  "technical_claims": [{{"claim": "type", "value": "val", "evidence": "why"}}],
  "tool_calls": [{{"thought": "why", "tool": "name", "input": "params"}}],
  "final_response": "answer if no tools needed"
}}

Available tools: {", ".join(tools)}

MANDATORY: Every technical claim (VRAM, NGL, Paths) MUST be listed in 'technical_claims'.
Failure to provide valid JSON or missing timestamps in 'thought' will result in rejection.
""",
        "timestamp": """
TEMPORAL ANCHORING:
Every response MUST start with a timestamp in this format: [H:MM AM/PM PT] (e.g., [1:20 PM PT])
Failure to use this format is a rule violation and will result in response rejection.
""",
        "citation": """
CITATION AND SOURCE REQUIREMENT:
For every piece of information or claim, cite the corresponding axis ID from the CONTEXT.
Format: [SRC:axis_N] (e.g., [SRC:axis_6], [SRC:axis_10])
""",
    }
