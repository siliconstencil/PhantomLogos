import asyncio

from src.muscle.local_runtime import LocalRuntime
from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client

logger = setup_logger(__name__)


async def _vision(bridge, input_data):
    try:
        from src.architrave.model_registry import get_vision_routing
        from src.utils.image_optimizer import optimize_image_for_vlm

        image_path = input_data.get("image_path") if isinstance(input_data, dict) else input_data
        prompt = (
            input_data.get("prompt", "Describe this image.")
            if isinstance(input_data, dict)
            else "Describe this image."
        )

        opt_path = await asyncio.to_thread(optimize_image_for_vlm, image_path)

        is_ocr = any(kw in prompt.lower() for kw in ["read", "ocr", "text", "document"])
        is_reasoning = any(
            kw in prompt.lower() for kw in ["diagram", "circuit", "logic", "reason", "math"]
        )
        is_creative = any(kw in prompt.lower() for kw in ["scene", "art", "creative", "style"])

        variant = (
            "thinking"
            if is_reasoning
            else "creative"
            if is_creative
            else "ocr"
            if is_ocr
            else "primary"
        )
        routing = get_vision_routing(variant)

        logger.info(
            f"ToolBridge: Routing to {variant} (model={routing['model']}, runtime={routing['runtime']})"
        )

        if routing["runtime"] == "local":
            if isinstance(input_data, dict):
                claimed_layers = input_data.get("layers")
                if claimed_layers is not None:
                    await bridge._shadow_verify_claim(
                        "ngl", claimed_layers, context={"model": routing["model"]}
                    )

            runtime = LocalRuntime()
            res = await runtime.run_vision_async(
                architecture=routing["architecture"],
                model_rel_path=routing["path"],
                mmproj_rel_path=routing["mmproj"],
                prompt=prompt,
                image_path=opt_path,
                num_ctx=input_data.get("num_ctx", 32768) if isinstance(input_data, dict) else 32768,
                registry_name=routing["model"],
                layers=routing["layers"],
            )

            if res and not str(res).startswith("Error"):
                from cognition.sophia.hephaestus import _get_visual

                visual = _get_visual()
                asyncio.create_task(
                    visual.store_vision(
                        image_path=image_path,
                        description=str(res),
                        variant=variant,
                        metadata={"prompt": prompt, "model": routing["model"]},
                        session_id=bridge.session_id,
                    )
                )
            return res
        else:
            model_name = bridge._resolve_model(routing["model"])
            logger.info(f"ToolBridge: Running Vision via Ollama (model={model_name})")

            def read_bytes(path):
                with open(path, "rb") as f:
                    return f.read()

            image_bytes = await asyncio.to_thread(read_bytes, opt_path)

            client = get_ollama_client()
            response = await client.generate(
                model=model_name, prompt=prompt, images=[image_bytes], stream=False
            )
            output = response.get("response", "")

            if output:
                from cognition.sophia.hephaestus import _get_visual

                visual = _get_visual()
                asyncio.create_task(
                    visual.store_vision(
                        image_path=image_path,
                        description=output,
                        variant=variant,
                        metadata={"prompt": prompt, "model": model_name},
                        session_id=bridge.session_id,
                    )
                )
            return output
    except Exception as e:
        logger.error(f"ToolBridge: Vision execution failed ({e})")
        return f"Vision execution error: {e!s}"
