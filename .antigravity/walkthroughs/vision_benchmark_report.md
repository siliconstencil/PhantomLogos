# Vision System Benchmark (Axis 14) Report

## Executive Summary
This benchmark evaluates the multimodal performance of the Sovereign OS vision pipeline across three different VLM models using a generated high-tech microchip test image.

## Model Performance Matrix

| Model | Variant | TTFT | Total Latency | Peak VRAM | Status |
|-------|---------|------|---------------|-----------|--------|
| **MiMo-VL** | thinking | N/A | N/A | 5.7 GB | **FAILED** (GGML_ASSERT) |
| **Qwen3-VL** | thinking | N/A | N/A | 3.4 GB | **FAILED** (Runner Stop) |
| **Qwen2.5-VL**| primary | 0.56s| 1.70s | 3.76 GB | **PASSED** |
| **Qwen2-VL-OCR**| ocr | 0.58s| 1.38s | 2.64 GB | **PASSED** |

## Critical Technical Findings
1. **MiMo-VL (K0.2 Error)**: Identified a low-level engine failure in Ollama:
   `GGML_ASSERT(hparams.n_pos_per_embd() == 1 && "seq_add() is only supported for n_pos_per_embd() == 1")`.
   *Action*: Marked MiMo-VL as "EXPERIMENTAL" in `model_registry` until llama.cpp fix is merged.

2. **VRAM Pressure**: Cold-starting `qwen3-vl-thinking` (3.4 GB) while IDE and background processes were active triggered an emergency Morpheus flush due to hitting the 7.0 GB Usable VRAM ceiling.

3. **Inference Speed**: Qwen2.5-VL demonstrated excellent responsiveness with a TTFT sub-0.6s, making it the recommended primary vision agent for real-time UI analysis.

## Content Accuracy
- **Text Recognition**: The model identified serial-like numbers ("1234567890") on the generated microchip. The prompt-specified "Antigravity OS" text was not clearly rendered by the generative model at 1024px, confirming standard resolution constraints.

---
**Verification Date**: 2026-05-12 [01:03 AM PT]
**Session ID**: test_vision_perf_v1
