"""End-to-end graph tests in demo mode (no API key), plus a retrieval regression suite."""

import asyncio
import json
import os
import re

import pytest

os.environ["LLM_PROVIDER"] = "demo"

from fastapi.testclient import TestClient  # noqa: E402

from app.graph import citation_check, run_agent  # noqa: E402
from app.knowledge import get_retriever, note_chunks, parse_note  # noqa: E402
from app.main import app  # noqa: E402

# Retrieval regression: each question must surface the expected chunk in the top 4.
RETRIEVAL_CASES = [
    ("What did Taniksha build at Bevi?", "exp-bevi"),
    ("Has Taniksha built an MCP server?", "exp-bevi"),
    ("Experience with Terraform and Airflow?", "proj-break-the-bot"),
    ("LLM safety and red teaming", "proj-break-the-bot"),
    ("Hidden Markov Model with Viterbi decoding", "proj-stack-overflow-auto-tagging"),
    ("What was the GPA at Northeastern?", "edu-northeastern"),
    ("Work on Hindi paraphrase generation", "exp-reverie"),
    ("Financial sentiment analysis research", "exp-pune"),
    ("Which programming languages?", "skills-languages"),
    ("Snowflake Cortex and dbt", "exp-bevi"),
    ("Undergraduate degree in computer engineering", "edu-savitribai"),
    ("Multilingual text detoxification with LoRA", "proj-multilingual-text-detoxification"),
    ("Music recommendation from Spotify listening history", "proj-spotify-recommendation-system"),
    ("Full stack marketplace with Express and MySQL", "proj-freelancer-client-platform"),
    ("Java design patterns", "proj-image-transformer-application"),
    ("What music does Taniksha listen to?", "about"),
    ("What are Taniksha's hobbies?", "about"),
    ("What kind of books does Taniksha read?", "about"),
    ("Where is Taniksha from?", "about"),
    # project write-ups in content/notes
    ("Why BM25 instead of embeddings?", "agent--retrieval"),
    ("How did Break The Bot validate data quality?", "proj-break-the-bot--data-quality-gates"),
    ("What evaluation metrics did the tagging project use?", "proj-stack-overflow-auto-tagging--evaluation-metrics"),
    ("Is there a live demo of the Stack Overflow tagger?", "proj-stack-overflow-auto-tagging--interactive-app"),
]


@pytest.mark.parametrize("question,expected", RETRIEVAL_CASES)
def test_retrieval_recall_at_4(question, expected):
    ids = [c.id for c, _ in get_retriever().search(question, k=4)]
    assert expected in ids, f"{expected} not in {ids}"


def collect(message, history=None):
    async def go():
        return [e async for e in run_agent(message, history or [])]

    return asyncio.run(go())


def nodes_run(events):
    return [e["node"] for e in events if e["type"] == "node_end"]


def test_question_path_streams_and_cites():
    events = collect("What agent systems did Taniksha build at Bevi?")
    assert nodes_run(events) == ["router", "retriever", "answerer", "citation_check"]
    assert any(e["type"] == "token" for e in events)
    result = events[-1]
    assert result["kind"] == "answer"
    source_ids = {src["id"] for src in result["sources"]}
    assert "exp-bevi" in source_ids
    cited = set(re.findall(r"\[([a-z0-9-]+)\]", result["text"]))
    assert cited and cited <= source_ids


def test_job_fit_path():
    jd = """Senior AI Engineer
    Requirements:
    - Experience building RAG systems and LLM agents
    - Strong Python and FastAPI
    - Kubernetes in production
    """
    events = collect(jd)
    assert nodes_run(events) == ["router", "extractor", "matcher", "citation_check"]
    result = events[-1]
    assert result["kind"] == "relevance" and len(result["items"]) >= 3
    assert all(isinstance(i["covered"], bool) for i in result["items"])
    assert "verdict" not in result["items"][0]  # points to work, never grades fit
    kube = next(i for i in result["items"] if "Kubernetes" in i["requirement"])
    assert kube["covered"] is False and kube["citations"] == []


def test_contact_path():
    events = collect("I'd like to email Taniksha about an interview")
    assert nodes_run(events) == ["router", "contact_drafter"]
    assert events[-1]["kind"] == "email" and events[-1]["to"] == "datar.t@northeastern.edu"


def test_off_topic_is_declined():
    events = collect("What's the weather in Paris?")
    assert nodes_run(events) == ["router", "guardrail"]


def test_citation_check_strips_and_downgrades(monkeypatch):
    state = {
        "chunks": [{"id": "exp-bevi"}],
        "answer": "Built agents [exp-bevi] and won awards [made-up].",
        "fit": {"summary": "", "items": [{"requirement": "Go", "covered": True, "evidence": "x", "citations": ["nope"]}]},
    }
    monkeypatch.setattr("app.graph.get_stream_writer", lambda: (lambda _event: None))
    out = asyncio.run(citation_check(state))
    assert out["answer"] == "Built agents [exp-bevi] and won awards."
    assert out["fit"]["items"][0]["covered"] is False
    assert set(out["removed_citations"]) == {"made-up", "nope"}


def test_http_stream_and_health():
    client = TestClient(app)
    assert client.get("/api/health").json()["demo"] is True
    with client.stream("POST", "/api/chat", json={"message": "What projects has Taniksha done?"}) as r:
        events = [json.loads(line[6:]) for line in r.iter_lines() if line.startswith("data: ")]
    assert events[-1]["type"] == "done"
    assert any(e["type"] == "result" for e in events)


def test_rejects_oversized_message():
    client = TestClient(app)
    assert client.post("/api/chat", json={"message": "x" * 7000}).status_code == 422


def test_note_sections_become_chunks_and_todos_are_skipped(tmp_path):
    (tmp_path / "demo.md").write_text(
        "---\ntarget: proj-demo\n---\n\n# Demo\n\n## Problem\nSolve it.\n\n## My part\nTODO\n", encoding="utf-8"
    )
    meta, title, sections = parse_note((tmp_path / "demo.md").read_text(encoding="utf-8"))
    assert meta["target"] == "proj-demo" and title == "Demo" and len(sections) == 2
    assert [c.id for c in note_chunks(tmp_path)] == ["proj-demo--problem"]


def test_real_notes_have_no_placeholder_chunks():
    assert all("TODO" not in c.text for c in note_chunks())


def test_questions_about_the_agent_pull_its_own_write_up():
    events = collect("How were you built?")
    retrieved = next(e for e in events if e.get("node") == "retriever" and e["type"] == "node_end")["detail"]
    assert "agent--architecture" in [c["id"] for c in retrieved]


def test_overview_requests_pull_the_core_profile():
    events = collect("Give me the 30-second version of Taniksha")
    retrieved = [c["id"] for c in next(e for e in events if e.get("node") == "retriever" and e["type"] == "node_end")["detail"]]
    assert {"top", "exp-bevi"} <= set(retrieved)


def test_grouped_citations_are_split_and_checked(monkeypatch):
    monkeypatch.setattr("app.graph.get_stream_writer", lambda: (lambda _event: None))
    state = {"chunks": [{"id": "top"}, {"id": "exp-bevi"}], "answer": "Builds LLM systems [top, exp-bevi, made-up]."}
    out = asyncio.run(citation_check(state))
    assert out["answer"] == "Builds LLM systems [top] [exp-bevi]."
    assert out["removed_citations"] == ["made-up"]


def test_router_prompt_treats_questions_about_the_agent_as_on_topic():
    from app.schemas import Route

    assert "this assistant (Nimbus)" in Route.model_fields["intent"].description


# ── provider fallback ───────────────────────────────────────────────────────

from app.demo_llm import DemoLLM  # noqa: E402
from app.llm import FallbackLLM, LLMUnavailable, is_quota_error  # noqa: E402
from app.schemas import Route  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402


class QuotaError(Exception):
    status_code = 429


class Broken:
    """A provider that always fails, counting how often it was tried."""

    def __init__(self, err):
        self.err, self.calls = err, 0

    def with_structured_output(self, schema, **_):
        outer = self

        class Runner:
            async def ainvoke(self, messages):
                outer.calls += 1
                raise outer.err

        return Runner()

    async def astream(self, messages):
        self.calls += 1
        raise self.err
        yield  # pragma: no cover - makes this an async generator


def route(llm):
    return asyncio.run(llm.with_structured_output(Route).ainvoke([HumanMessage("<message>What projects has Taniksha built?</message>")]))


def test_falls_back_and_cools_down_an_exhausted_provider():
    broken = Broken(QuotaError("429 rate limit reached"))
    llm = FallbackLLM([("groq", broken), ("backup", DemoLLM())], cooldown_seconds=600)
    assert route(llm).intent == "question"  # answered by the backup
    assert broken.calls == 1 and "groq" in llm.cooling_until
    route(llm)
    assert broken.calls == 1  # skipped while cooling down


def test_non_quota_errors_fall_back_without_cooldown():
    broken = Broken(ConnectionError("timeout"))
    llm = FallbackLLM([("groq", broken), ("backup", DemoLLM())])
    route(llm)
    route(llm)
    assert broken.calls == 2 and not llm.cooling_until


def test_streaming_falls_back_before_the_first_token():
    llm = FallbackLLM([("groq", Broken(QuotaError("quota"))), ("backup", DemoLLM())])

    async def collect():
        return "".join([c.content async for c in llm.astream([HumanMessage("<context>\n</context>\nQuestion: hi")])])

    assert asyncio.run(collect())


def test_every_provider_failing_raises_llm_unavailable():
    llm = FallbackLLM([("a", Broken(QuotaError("429"))), ("b", Broken(QuotaError("402 credits")))])
    with pytest.raises(LLMUnavailable):
        route(llm)


def test_quota_error_detection():
    assert is_quota_error(QuotaError("x"))
    assert is_quota_error(Exception("This request requires more credits"))
    assert not is_quota_error(ConnectionError("timeout"))


def test_retired_model_or_bad_key_is_skipped_after_first_failure():
    class NotFound(Exception):
        status_code = 404

    broken = Broken(NotFound("model_not_found"))
    llm = FallbackLLM([("groq", broken), ("backup", DemoLLM())])
    route(llm)
    route(llm)
    assert broken.calls == 1


def test_rate_limits_back_off_briefly_not_for_the_long_cooldown():
    broken = Broken(QuotaError("429 tokens per minute"))
    llm = FallbackLLM([("groq", broken), ("backup", DemoLLM())], cooldown_seconds=600)
    route(llm)
    import time as _t

    assert llm.cooling_until["groq"] - _t.monotonic() <= 61


def test_fullwidth_citations_and_name_misspelling_are_fixed(monkeypatch):
    monkeypatch.setattr("app.graph.get_stream_writer", lambda: (lambda _event: None))
    state = {"chunks": [{"id": "about"}], "answer": "Tanisha builds AI【about】."}
    out = asyncio.run(citation_check(state))
    assert out["answer"] == "Taniksha builds AI [about]."
