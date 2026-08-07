---
kind: external_dependency
name: PyTorch — ML runtime used by the Transformers backend
slug: pytorch
category: external_dependency
category_hints:
    - vendor_identity
scope:
    - '**'
---

### Identity + role
- Used implicitly through `transformers`/`accelerate`; no direct torch API calls in this repo beyond device/dtype checks.

### Integration point
- No direct model code owns tensors; all inference is delegated to `transformers.AutoModelForCausalLM`.

### Durable note
- If moving away from the transformers backend, remove the `torch` dependency; the mock backend has no torch requirement.