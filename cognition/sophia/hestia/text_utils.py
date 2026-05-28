import json
import re


def strip_thinking_block(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def extract_first_json_block(text: str) -> str | None:
    brace_depth = 0
    json_start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if brace_depth == 0:
                json_start = i
            brace_depth += 1
        elif ch == "}":
            brace_depth -= 1
            if brace_depth == 0 and json_start >= 0:
                return text[json_start : i + 1]
    return None


def extract_tool_calls(text: str) -> list[dict]:
    results = []
    start_idx = 0
    while True:
        idx = text.find("{", start_idx)
        if idx == -1:
            break

        depth = 0
        end_idx = -1
        for i in range(idx, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break

        if end_idx != -1:
            snippet = text[idx:end_idx]
            try:
                data = json.loads(snippet)
                if isinstance(data, dict) and "tool" in data and "input" in data:
                    results.append(data)
            except json.JSONDecodeError:
                pass
            start_idx = end_idx
        else:
            start_idx = idx + 1

    return results
