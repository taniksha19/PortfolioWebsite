"""Chat model selection with automatic fallback across providers.

Providers are tried in order (Groq, then Google, then OpenRouter by default, using whichever API keys
are set). If one fails, the next answers instead. A provider that runs out of quota or credit
(429/402) is skipped for a cool-down period so later requests don't keep waiting on it.

LLM_PROVIDERS="groq,openrouter" sets the order explicitly; LLM_PROVIDER picks a single provider.
"""

import logging
import os
import time
from functools import lru_cache

log = logging.getLogger("portfolio-agent.llm")

PREFERRED_ORDER = ["groq", "google", "openrouter"]
KEY_FOR = {"groq": "GROQ_API_KEY", "google": "GOOGLE_API_KEY", "openrouter": "OPENROUTER_API_KEY"}
COOLDOWN_SECONDS = int(os.getenv("LLM_COOLDOWN_SECONDS", "600"))  # bad key, retired model, out of credit
RATE_LIMIT_COOLDOWN = 60  # per-minute limits reset quickly; used when the provider doesn't say when


class LLMUnavailable(RuntimeError):
    """Every provider in the chain failed for this request."""


def providers() -> list[str]:
    explicit = os.getenv("LLM_PROVIDERS") or os.getenv("LLM_PROVIDER") or ""
    chosen = [p.strip().lower() for p in explicit.split(",") if p.strip()]
    if not chosen:
        chosen = [p for p in PREFERRED_ORDER if os.getenv(KEY_FOR[p])]
    return chosen or ["demo"]


def provider() -> str:
    return providers()[0]


def model_for(p: str, primary: bool) -> str:
    if p == "openrouter":
        # As a backup, OpenRouter uses a free model so it never drains credit.
        default = "google/gemini-2.5-flash" if primary else "nvidia/nemotron-3-super-120b-a12b:free"
        env = "OPENROUTER_MODEL" if primary else "OPENROUTER_FALLBACK_MODEL"
        return os.getenv(env, default)
    return {
        "google": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "groq": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    }.get(p, "demo")


def model_name() -> str:
    chain = providers()
    backups = len(chain) - 1
    return model_for(chain[0], True) + (f" +{backups} backup{'s' if backups > 1 else ''}" if backups else "")


def _build(p: str, model: str):
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1500"))
    if p == "openrouter":
        from langchain_openai import ChatOpenAI

        class ChatOpenRouter(ChatOpenAI):
            # Tool calling is supported by far more OpenRouter models than strict JSON-schema mode.
            def with_structured_output(self, schema, *, method="function_calling", **kwargs):
                return super().with_structured_output(schema, method=method, **kwargs)

        return ChatOpenRouter(
            model=model,
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
            temperature=0.2,
            # Without a cap OpenRouter reserves the model's full output limit against your credits.
            # Sent as OpenRouter's `max_tokens`; it ignores OpenAI's newer `max_completion_tokens`.
            extra_body={"max_tokens": max_tokens},
            max_retries=0,
            timeout=30,
            default_headers={"HTTP-Referer": os.getenv("SITE_URL", "http://localhost:5173"), "X-Title": "Taniksha Datar portfolio agent"},
        )
    if p == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=model, temperature=0.2, max_output_tokens=max_tokens, max_retries=0, timeout=30)
    if p == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(model=model, temperature=0.2, max_tokens=max_tokens, max_retries=0, timeout=30)
    if p == "demo":
        from .demo_llm import DemoLLM

        return DemoLLM()
    raise ValueError(f"Unknown LLM provider: {p!r} (use groq, google, openrouter or demo)")


def _status(err: Exception):
    return getattr(err, "status_code", None) or getattr(getattr(err, "response", None), "status_code", None)


def is_quota_error(err: Exception) -> bool:
    text = str(err).lower()
    return _status(err) in (402, 429) or any(s in text for s in ("rate limit", "rate-limit", "quota", "credits", "resource_exhausted"))


def retry_after(err: Exception) -> float | None:
    headers = getattr(getattr(err, "response", None), "headers", None) or {}
    try:
        return float(headers.get("retry-after"))
    except (TypeError, ValueError):
        return None


def is_config_error(err: Exception) -> bool:
    """Bad key, no access, or a retired model: retrying won't help until someone fixes the setup."""
    return _status(err) in (401, 403, 404) or "model_not_found" in str(err).lower()


class FallbackLLM:
    """Tries each (label, model) in order; mirrors the two calls the graph makes:
    .with_structured_output(schema).ainvoke(...) and .astream(...)."""

    def __init__(self, entries, cooldown_seconds: int = COOLDOWN_SECONDS):
        self.entries = entries
        self.cooldown_seconds = cooldown_seconds
        self.cooling_until: dict[str, float] = {}

    def _order(self, entries):
        now = time.monotonic()
        ready = [e for e in entries if self.cooling_until.get(e[0], 0) <= now]
        # If everything is cooling down, try them all anyway rather than refusing outright.
        return ready or list(entries)

    def _failed(self, label: str, err: Exception) -> None:
        if _status(err) == 429:
            # Rate limited: back off for as long as the provider asks (Groq's per-minute token limit
            # usually clears within a minute), not the long cool-down meant for broken setups.
            wait = min(retry_after(err) or RATE_LIMIT_COOLDOWN, self.cooldown_seconds)
            self.cooling_until[label] = time.monotonic() + wait
            log.warning("LLM %s is rate limited; skipping it for %.0fs", label, wait)
        elif is_quota_error(err) or is_config_error(err):
            self.cooling_until[label] = time.monotonic() + self.cooldown_seconds
            reason = "is out of quota" if is_quota_error(err) else f"is misconfigured ({str(err)[:120]})"
            log.warning("LLM %s %s; skipping it for %ss", label, reason, self.cooldown_seconds)
        else:
            log.warning("LLM %s failed (%s: %s); trying the next one", label, type(err).__name__, str(err)[:200])

    def with_structured_output(self, schema, **kwargs):
        return _FallbackStructured(self, [(label, llm.with_structured_output(schema, **kwargs)) for label, llm in self.entries])

    async def astream(self, messages):
        last = None
        for label, llm in self._order(self.entries):
            started = False
            try:
                async for chunk in llm.astream(messages):
                    started = True
                    yield chunk
                return
            except Exception as err:  # noqa: BLE001 - any provider error should fall through to the next
                if started:
                    raise  # can't switch providers halfway through a visible answer
                self._failed(label, err)
                last = err
        raise LLMUnavailable("All language model providers failed") from last


class _FallbackStructured:
    def __init__(self, parent: FallbackLLM, entries):
        self.parent = parent
        self.entries = entries

    async def ainvoke(self, messages):
        last = None
        for label, runnable in self.parent._order(self.entries):
            try:
                return await runnable.ainvoke(messages)
            except Exception as err:  # noqa: BLE001
                self.parent._failed(label, err)
                last = err
        raise LLMUnavailable("All language model providers failed") from last


@lru_cache
def get_llm():
    chain = providers()
    if chain == ["demo"]:
        return _build("demo", "demo")
    return FallbackLLM([(f"{p}:{model_for(p, i == 0)}", _build(p, model_for(p, i == 0))) for i, p in enumerate(chain)])
