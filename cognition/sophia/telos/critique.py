import asyncio
import json
import os
import time

import yaml

from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client

from ..eidos import CritiqueResult
from ..gnosis import get_dynamic_context
from ..hephaestus import _get_procedural, extract_first_json_block

logger = setup_logger(__name__)


async def run_critique(
    draft: str, session_id: str = "default", model_name: str | None = None
) -> CritiqueResult:
    logger.info(f"Sophia: Auditing Draft in session {session_id}...")
    critique_start = time.time()
    stable, dynamic, _ = await get_dynamic_context("auditor", session_id=session_id)

    skill_context = ""
    try:
        with open(os.path.join("agent", "lachesis.yaml")) as f:
            cfg = yaml.safe_load(f)
        skills_list = cfg.get("skills", [])
        if skills_list:
            from src.clotho.skill_loader import get_skill_loader

            loader = get_skill_loader()
            summaries = [
                loader.get_skill_summary(s) for s in skills_list if loader.get_skill_summary(s)
            ]
            if summaries:
                skill_context = "ACTIVE SKILLS:\n" + "\n".join([s for s in summaries if s])
    except Exception:
        pass

    context = f"{stable}\n\n{skill_context}\n\n{dynamic}"

    from src.clotho.bootstrap import get_scheduler

    get_scheduler()
    from src.architrave.model_registry import resolve_local_model

    model_name = model_name or resolve_local_model("critique", "primary")

    response = await asyncio.wait_for(
        get_ollama_client().chat(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": f"You are the Logical Auditor (Lachesis).\n\nCONTEXT:\n{context}\n\nReturn JSON: is_valid, flaws, suggestions.",
                },
                {"role": "user", "content": f"Review this draft:\n{draft}"},
            ],
        ),
        timeout=30.0,
    )

    _get_procedural().record_usage(
        tool_name="phi-4-mini-ud",
        task_type="critique",
        success=True,
        latency_ms=round((time.time() - critique_start) * 1000, 1),
    )

    content = response["message"]["content"]
    try:
        json_str = extract_first_json_block(content)
        if not json_str:
            return CritiqueResult(
                is_valid=False, flaws=["Parse Error"], suggestions=[content], confidence_score=0.1
            )

        res_data = json.loads(json_str)

        flaw_count = len(res_data.get("flaws", []))
        is_valid = res_data.get("is_valid", False)

        conf = 1.0 - (flaw_count * 0.15)
        if not is_valid:
            conf = min(conf, 0.6)

        conf = max(0.1, round(conf, 2))
        res_data["confidence_score"] = conf

        return CritiqueResult(**res_data)
    except Exception as e:
        logger.error(f"Sophia: Critique parsing failed ({e})")
        return CritiqueResult(
            is_valid=False, flaws=[str(e)], suggestions=[content], confidence_score=0.1
        )
