"""
llm_providers — one small adapter per AI provider.

Each adapter exposes the same tiny contract, so llm.py can treat them
interchangeably:

    NAME: str                 # short tag used in log lines
    available() -> bool       # is this provider usable right now?
    run(prompt: str) -> str   # send the prompt, return raw model text (raise on failure)

The shared prompt, JSON parsing, provider selection, and rule-based fallback all live
in llm.py — adapters only know how to call their own model. To add a provider, drop a
new module here implementing the three names above and register it in llm.py.
"""
