# Scratchbook: Phase 11.18.4 SovereignTruthGuard Tracking
*Status: INITIALIZED*

## [ ] Step 1: Shadow Verification (Hardware Truth)
- [ ] **S1.1: output_guard.py**
    - [ ] Add `VIOLATION_SHADOW_VERIFY = "shadow_verification_failed"`
    - [ ] Map violation to `reliability_impact = -0.3`
- [ ] **S1.2: tool_bridge.py**
    - [ ] Add `from src.clotho.bootstrap import get_loader`
    - [ ] Implement `_shadow_verify_claim(self, claim_type, claimed_val)`
    - [ ] Logic for `vram` type: check `nvidia-smi` vs `claimed_val`
    - [ ] Logic for `ngl` type: check registry/math vs `claimed_val`
    - [ ] Update `_vision()` and `_vram()` to call `_shadow_verify_claim()`
    - [ ] Trigger `loader.flush()` on mismatch

## [ ] Step 2: Pydantic Schema (The Contract)
- [ ] **S2.1: hephaestus.py**
    - [ ] Create `TechnicalClaim(BaseModel)`: `claim, value, verified, evidence`
    - [ ] Create `SophiaOutput(BaseModel)`: `thought, claims, tool_calls, final_response`
- [ ] **S2.2: sophia.py**
    - [ ] Update `run_draft` to use Pydantic parsing
    - [ ] Implement `record_inconsistency()` to Axis 11 on verification failure

## [ ] Step 3: Hard Gates & Blacklists (The Authority)
- [ ] **S3.1: gnosis.py**
    - [ ] Update `_build_axis_8_failures` to return `block_signal`
    - [ ] Logic: If severity >= 3 and recurrence >= 3 -> Block
- [ ] **S3.2: krisis.py**
    - [ ] Add `bypass_memory_gate` handling
    - [ ] Implement `BLACKLISTED_MODELS` state tracking
    - [ ] Update `should_use_tier` to skip blacklisted models and use fallbacks

## [ ] Step 4: Auto-Rotation (The Evolution)
- [ ] **S4.1: self_tuner.py**
    - [ ] Transform `_suggest_model_change` into an actionable command
    - [ ] Update `adjust_reliability` to trigger rotation after 2 shadow failures
- [ ] **S4.2: Final Integration Test**
    - [ ] Run "Lies & Truth" battery test

---
*Next Action: S1.1: output_guard.py update*
