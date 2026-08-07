---
kind: external_dependency
name: Hugging Face Transformers — Real LLM backend via HF Hub
slug: huggingface-transformers
category: external_dependency
category_hints:
    - vendor_identity
    - sdk_real_api
scope:
    - '**'
---

### Identity + role
- The project ships two LLM backends: a `MockBackend` for demo/testing and a `TransformersBackend` that loads a real causal LM from Hugging Face Hub.
- Default model is `Qwen/Qwen2.5-0.5B-Instruct`; can be overridden via `HARNESS_MODEL_NAME`.

### Integration point
- Device selection auto-picks CUDA → MPS → CPU; dtype switches to float16 on GPU.
- Chat formatting goes through the tokenizer's built-in `apply_chat_template`, so each model family (Qwen, Llama, etc.) gets its own prompt shape automatically.

### Durable usage pattern
- Switch backends at runtime via the `HARNESS_LLM_BACKEND` env var (`mock` vs `transformers`).
- When using the transformers backend, first run downloads ~1 GB of model weights into the HF cache before any demo works.
- Verify exact model loading args / chat template behavior against the official `transformers` docs for the chosen model.