# Embedding Zero-Vector Fallback Test Plan

This document was prepared to verify, as part of K1.4, that when embedding generation returns an empty list or produces a zero vector, the system (matryoshka, theoria, etc.) switches to a safe fallback state and keeps running. [2:45 PM PT]

## 1. Test Scenarios

### Scenario A: SLM Client Empty List Fallback Test
- **Steps:**
  1. Run the smoke test in `tests/test_zero_vector.py`:
     `.venv\Scripts\pytest.exe tests/test_zero_vector.py -v`
  2. Verify that the test mocks the SLMClient.embed() method to return an empty list and that the matryoshka/theoria components switch to the local fallback model without raising an error.
- **Expected Result:** The test must pass and the logs must show that the fallback state is active.
