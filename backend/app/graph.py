"""The portfolio agent, as a LangGraph state graph.

    router ──question──▶ retriever ──▶ answerer ─────┐
       │ ──job_fit────▶ extractor ──▶ matcher ───────┼─▶ citation_check ─▶ END
       │ ──contact────▶ contact_drafter ─────────────┼──────────────────▶ END
       └ ──off_topic──▶ guardrail ───────────────────┘

Each node reports start/finish events through LangGraph's custom stream so the frontend can
animate the graph and show a live trace.
"""

import re
import time
from functools import wraps
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph

from .knowledge import Chunk, get_retriever, load_content
from .llm import get_llm
from .schemas import EmailDraft, RelevanceReport, Requirements, Route

PERSONA = (
    "You are Nimbus, the portfolio assistant for Taniksha Datar, an AI engineer. Spell the name exactly "
    "'Taniksha'. Taniksha uses she/her pronouns. Use only the provided context; never invent "
    "employers, numbers, dates or skills. Work experience and solo projects are Taniksha's own work. Only a "
    "project whose context has a 'Team' section was built by a team: describe that work as the team's, and "
    "never credit Taniksha with a specific part of it unless the context says it was hers. When asked about "
    "yourself or how you work, answer from the 'How this agent works' context."
)

# Questions about the agent itself ("how were you built?") and broad overview requests need
# context that keyword search won't find on its own.
SELF_RE = re.compile(r"\b(you|your|yourself|nimbus|this agent|this bot|this chatbot|this site|this website|this portfolio)\b", re.I)
OVERVIEW_RE = re.compile(r"\b(30.second|overview|summary|summari[sz]e|tl;?dr|quick version|introduce|who is)\b", re.I)
SELF_IDS = ["agent--overview", "agent--architecture", "agent--retrieval", "agent--grounding-and-citations"]
OVERVIEW_IDS = ["top", "exp-bevi", "proj-break-the-bot", "proj-multilingual-text-detoxification", "about"]


class AgentState(TypedDict, total=False):
    message: str
    history: list[dict]
    intent: str
    route_reason: str
    chunks: list[dict]
    answer: str
    role_title: str
    requirements: list[str]
    fit: dict
    email: dict
    removed_citations: list[str]


def traced(name: str, describe=None):
    """Emit node_start / node_end events (with timing and a short detail) around a node."""

    def decorator(fn):
        @wraps(fn)
        async def wrapper(state: AgentState) -> dict:
            write = get_stream_writer()
            write({"type": "node_start", "node": name})
            t0 = time.perf_counter()
            update = await fn(state)
            write(
                {
                    "type": "node_end",
                    "node": name,
                    "ms": round((time.perf_counter() - t0) * 1000),
                    "detail": describe(update) if describe else None,
                }
            )
            return update

        return wrapper

    return decorator


def _format_chunks(chunks: list[dict]) -> str:
    return "\n\n".join(f"[{c['id']}] {c['title']}\n{c['text']}" for c in chunks)


def _history_text(history: list[dict]) -> str:
    return "\n".join(f"{'Visitor' if h['role'] == 'user' else 'Assistant'}: {h['content']}" for h in history)


def _chunk_dict(chunk: Chunk, score: float) -> dict:
    return {"id": chunk.id, "title": chunk.title, "text": chunk.text, "score": round(score, 2)}


def _token_text(chunk: Any) -> str:
    text = getattr(chunk, "text", None)
    if isinstance(text, str):
        return text
    content = getattr(chunk, "content", "")
    if isinstance(content, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return content or ""


# ── nodes ────────────────────────────────────────────────────────────────────


@traced("router", lambda u: f"{u['intent']}: {u['route_reason']}")
async def router(state: AgentState) -> dict:
    prompt = (
        f"Classify the visitor's latest message.\n\n<history>\n{_history_text(state.get('history', []))}\n</history>\n\n"
        f"<message>\n{state['message']}\n</message>"
    )
    route: Route = await get_llm().with_structured_output(Route).ainvoke(
        [SystemMessage(PERSONA + " You route messages to the right specialist."), HumanMessage(prompt)]
    )
    return {"intent": route.intent, "route_reason": route.reason}


@traced("retriever", lambda u: [{"id": c["id"], "score": c["score"]} for c in u["chunks"]])
async def retriever(state: AgentState) -> dict:
    retr = get_retriever()
    # Include the previous visitor turn so follow-ups like "what stack did that use?" still retrieve.
    prev = [h["content"] for h in state.get("history", []) if h["role"] == "user"][-1:]
    msg = state["message"]
    hits = retr.search(" ".join(prev + [msg]), k=5)
    pinned = (SELF_IDS if SELF_RE.search(msg) else []) + (OVERVIEW_IDS if OVERVIEW_RE.search(msg) else [])
    seen = {c.id for c, _ in hits}
    extra = [(retr.by_id[i], 0.0) for i in pinned if i in retr.by_id and i not in seen]
    return {"chunks": [_chunk_dict(c, s) for c, s in extra + hits][:8]}


@traced("answerer", lambda u: f"{len(u['answer'].split())} words")
async def answerer(state: AgentState) -> dict:
    write = get_stream_writer()
    system = (
        PERSONA + " Answer in 2-5 sentences. After each claim, cite the supporting chunk id in square "
        "brackets, one id per bracket, e.g. [exp-bevi] [proj-break-the-bot]. If the visitor asks for a quick version or plain language, keep it short "
        "and jargon-free. Do not guess at reasons, causes or details the context doesn't state; if it says what "
        "happened but not why, say the portfolio doesn't explain why. If the context does not answer the question, "
        "say you don't know and suggest emailing Taniksha. Do not cite ids that are not in the context."
    )
    prompt = (
        f"<context>\n{_format_chunks(state['chunks'])}\n</context>\n\n"
        f"<history>\n{_history_text(state.get('history', []))}\n</history>\n\nQuestion: {state['message']}"
    )
    parts = []
    async for chunk in get_llm().astream([SystemMessage(system), HumanMessage(prompt)]):
        text = _token_text(chunk)
        if text:
            parts.append(text)
            write({"type": "token", "text": text})
    return {"answer": "".join(parts).strip()}


@traced("extractor", lambda u: f"{len(u['requirements'])} requirements")
async def extractor(state: AgentState) -> dict:
    reqs: Requirements = await get_llm().with_structured_output(Requirements).ainvoke(
        [
            SystemMessage(PERSONA + " Extract the concrete requirements from a job description."),
            HumanMessage(f"<job_description>\n{state['message']}\n</job_description>"),
        ]
    )
    return {"role_title": reqs.role_title, "requirements": reqs.requirements[:8]}


@traced("matcher", lambda u: {"covered": sum(i["covered"] for i in u["fit"]["items"]), "not_shown": sum(not i["covered"] for i in u["fit"]["items"])})
async def matcher(state: AgentState) -> dict:
    retr = get_retriever()
    blocks, seen = [], {}
    for req in state["requirements"]:
        hits = retr.search(req, k=4)
        for c, s in hits:
            seen.setdefault(c.id, _chunk_dict(c, s))
        evidence = "\n".join(f"[{c.id}] (score {s:.2f}) {c.title}" for c, s in hits) or "(no matches)"
        blocks.append(f'<requirement text="{req.replace(chr(34), chr(39))}">\n{evidence}\n</requirement>')
    system = (
        PERSONA + " A visitor pasted a role. Help them find the parts of Taniksha's portfolio that are relevant "
        "to each requirement. Do not judge fit, rate, score or recommend hiring; just point to the evidence. "
        "For each requirement set covered=true and cite where it shows up, or covered=false if the portfolio "
        "does not show it. Prefer concrete evidence from work experience and projects over the general profile "
        "or skills list. Cite only chunk ids from the context."
    )
    prompt = (
        f"<context>\n{_format_chunks(list(seen.values()))}\n</context>\n\n"
        f"Requirements for {state['role_title']}, each with the retrieved candidate evidence:\n" + "\n".join(blocks)
    )
    report: RelevanceReport = await get_llm().with_structured_output(RelevanceReport).ainvoke([SystemMessage(system), HumanMessage(prompt)])
    return {"fit": report.model_dump(), "chunks": list(seen.values())}


@traced("contact_drafter", lambda u: u["email"]["subject"])
async def contact_drafter(state: AgentState) -> dict:
    convo = _history_text(state.get("history", []) + [{"role": "user", "content": state["message"]}])
    draft: EmailDraft = await get_llm().with_structured_output(EmailDraft).ainvoke(
        [
            SystemMessage(PERSONA + " Draft an email the visitor can send to Taniksha, based on the conversation."),
            HumanMessage(f"<conversation>\n{convo}\n</conversation>"),
        ]
    )
    return {"email": {**draft.model_dump(), "to": load_content()["profile"]["email"]}}


@traced("guardrail", lambda u: "declined")
async def guardrail(state: AgentState) -> dict:
    return {
        "answer": "I can only talk about Taniksha: work, projects, skills, education and interests. "
        "Try asking about the agent systems at Bevi, or paste a job description to check fit."
    }


@traced("citation_check", lambda u: {"removed": u["removed_citations"]})
async def citation_check(state: AgentState) -> dict:
    """Deterministic grounding check: drop any citation that doesn't point at retrieved context."""
    valid = {c["id"] for c in state.get("chunks", [])}
    removed: list[str] = []
    update: dict = {}

    if state.get("answer"):

        def keep(m: re.Match) -> str:
            if m.group(1) in valid:
                return m.group(0)
            removed.append(m.group(1))
            return ""

        # Some models write citations as 【id】; normalise them to [id].
        answer = re.sub(r" *【\s*([a-z0-9-]+)\s*】", r" [\1]", state["answer"].replace("­", ""))  # also drop soft hyphens
        # Models sometimes group ids as "[a, b]"; split them so each one is checked and rendered.
        answer = re.sub(r"\[([a-z0-9-]+(?:\s*,\s*[a-z0-9-]+)+)\]", lambda m: " ".join(f"[{i.strip()}]" for i in m.group(1).split(",")), answer)
        answer = re.sub(r"\bTanisha\b", "Taniksha", answer)  # a common misspelling
        update["answer"] = re.sub(r"\s?\[([a-z0-9-]+)\]", keep, answer).strip()

    if state.get("fit"):
        items = []
        for item in state["fit"]["items"]:
            good = [c for c in item["citations"] if c in valid]
            removed += [c for c in item["citations"] if c not in valid]
            if item["covered"] and not good:
                # A requirement with no surviving evidence isn't shown by the portfolio.
                item = {**item, "covered": False, "evidence": "Not shown in the portfolio."}
            items.append({**item, "citations": good})
        update["fit"] = {**state["fit"], "items": items}

    update["removed_citations"] = removed
    return update


# ── wiring ───────────────────────────────────────────────────────────────────


def build_graph():
    g = StateGraph(AgentState)
    for name, fn in [
        ("router", router),
        ("retriever", retriever),
        ("answerer", answerer),
        ("extractor", extractor),
        ("matcher", matcher),
        ("contact_drafter", contact_drafter),
        ("guardrail", guardrail),
        ("citation_check", citation_check),
    ]:
        g.add_node(name, fn)

    g.add_edge(START, "router")
    g.add_conditional_edges(
        "router",
        lambda s: s["intent"],
        {"question": "retriever", "job_fit": "extractor", "contact": "contact_drafter", "off_topic": "guardrail"},
    )
    g.add_edge("retriever", "answerer")
    g.add_edge("answerer", "citation_check")
    g.add_edge("extractor", "matcher")
    g.add_edge("matcher", "citation_check")
    g.add_edge("citation_check", END)
    g.add_edge("contact_drafter", END)
    g.add_edge("guardrail", END)
    return g.compile()


graph = build_graph()


async def run_agent(message: str, history: list[dict]):
    """Yield UI events: node_start/node_end/token from the nodes, then one final result."""
    final: AgentState = {}
    async for mode, payload in graph.astream({"message": message, "history": history}, stream_mode=["custom", "values"]):
        if mode == "custom":
            yield payload
        else:
            final = payload

    sources = [{"id": c["id"], "title": c["title"]} for c in final.get("chunks", [])]
    intent = final.get("intent")
    if intent == "job_fit":
        yield {"type": "result", "kind": "relevance", "role_title": final["role_title"], **final["fit"], "sources": sources}
    elif intent == "contact":
        yield {"type": "result", "kind": "email", **final["email"]}
    else:
        yield {"type": "result", "kind": "answer", "text": final.get("answer", ""), "sources": sources}
