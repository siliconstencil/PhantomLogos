import requests
import json
import time

def benchmark_model(model_name, prompt):
    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "top_p": 0.8
        }
    }
    
    start_time = time.monotonic()
    try:
        response = requests.post(url, json=payload, timeout=30)
        latency = time.monotonic() - start_time
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result.get("response", ""),
                "latency": latency,
                "tokens": result.get("eval_count", 0)
            }
        return {"success": False, "error": f"Status: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_exam():
    model = "qwen2.5-coder-0.5b"
    print(f"--- [EXAM] Model: {model} Efficiency Test ---")
    
    test_cases = [
        {
            "name": "Logic Contradiction",
            "prompt": "Analyze this Python code for logic flaws: \nif x > 10 and x < 5:\n    print('Impossible')",
            "expected": "contradiction"
        },
        {
            "name": "Math Accuracy",
            "prompt": "Does this code have a math error? \ndef calculate():\n    return 2 + 2 * 3 # expected 8, but actual is 8? wait 2 + 6 = 8. \n    # let's try a real error: \n    res = (10 / 2) + 5\n    if res != 10: return 'error'",
            "expected": "no error"
        },
        {
            "name": "Security Flaw",
            "prompt": "Identify security risks: \nimport os\ndef read_file(name):\n    with open('../data/' + name, 'r') as f: return f.read()",
            "expected": "path traversal"
        }
    ]
    
    for tc in test_cases:
        print(f"\nRunning Test: {tc['name']}...")
        res = benchmark_model(model, tc["prompt"])
        if res["success"]:
            print(f"Latency: {res['latency']:.2f}s")
            print(f"Tokens: {res['tokens']}")
            print(f"Analysis: {res['response'][:200]}...")
        else:
            print(f"FAILED: {res['error']}")

if __name__ == "__main__":
    run_exam()
