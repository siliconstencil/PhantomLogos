import asyncio
from typing import Any
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

async def _verify(bridge, input_data):
    try:
        from src.lachesis.verifiers import SympyVerifier
        verifier = SympyVerifier()
        task = input_data.get("task") if isinstance(input_data, dict) else str(input_data)
        expr = input_data.get("expression") if isinstance(input_data, dict) else ""
        if task == "math" and expr:
            return await asyncio.to_thread(verifier.verify_expression, expr)
        if task == "solve" and expr:
            return await asyncio.to_thread(verifier.verify_math, expr)
        
        coder_model = bridge._resolve_model("qwen-7b")
        verifier = SympyVerifier(model=coder_model)
        return await asyncio.to_thread(verifier.audit_code_logic, input_data.get("code", "") if isinstance(input_data, dict) else str(input_data))
    except Exception as e:
        return f"Verify error: {str(e)}"
