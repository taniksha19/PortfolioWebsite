"""A keyless stand-in for the chat model, used for local development, tests and demo deploys.

It is not a language model: it reads the same prompts the real model gets and answers with
simple rules, so the whole graph (routing, retrieval, fit scoring, citation checks, streaming)
runs end to end without an API key.
"""

import asyncio
import re
from types import SimpleNamespace

from .schemas import EmailDraft, RelevanceReport, RelevantWork, Requirements, Route

JOB_HINTS = ("responsibilit", "requirement", "qualification", "job description", "we are looking", "you will", "years of experience", "nice to have")
CONTACT_HINTS = ("email", "contact", "reach out", "reach her", "get in touch", "hire", "interview", "schedule", "connect with")
TOPIC_HINTS = ("taniksha", "experience", "project", "skill", "work", "built", "study", "school", "education", "gpa", "degree", "intern", "co-op",
               "she", "her", "they", "their", "fun", "hobby", "hobbies", "music", "books", "read", "from", "puzzle", "you", "agent", "llm", "rag", "mlops", "python", "cloud", "model", "data", "bevi", "resume")


def _last_human(messages) -> str:
    return next((m.content for m in reversed(messages) if m.type == "human"), "")


def _between(text: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.S)
    return m.group(1).strip() if m else ""


class _Structured:
    def __init__(self, schema):
        self.schema = schema

    async def ainvoke(self, messages):
        await asyncio.sleep(0.35)  # make the trace animation visible
        text = _last_human(messages)
        return getattr(self, f"_{self.schema.__name__}")(text)

    def _Route(self, text):
        msg = _between(text, "message").lower() or text.lower()
        if len(msg) > 350 or any(h in msg for h in JOB_HINTS):
            return Route(intent="job_fit", reason="Looks like a job description.")
        if any(h in msg for h in CONTACT_HINTS):
            return Route(intent="contact", reason="Visitor wants to get in touch.")
        if any(re.search(rf"\b{re.escape(h)}\b", msg) for h in TOPIC_HINTS):
            return Route(intent="question", reason="A question about Taniksha's background.")
        return Route(intent="off_topic", reason="Not about Taniksha.")

    def _Requirements(self, text):
        jd = _between(text, "job_description")
        lines = [re.sub(r"^[\s\-*•\d.)]+", "", l).strip() for l in jd.splitlines()]
        reqs = [l for l in lines if 2 <= len(l.split()) <= 25 and not l.endswith(":")]
        if not reqs:
            reqs = [s.strip() for s in re.split(r"[.;]\s+", jd) if len(s.split()) >= 3]
        return Requirements(role_title="the role", requirements=[" ".join(r.split()[:12]) for r in reqs[:6]])

    def _RelevanceReport(self, text):
        items = []
        for req, evidence in re.findall(r'<requirement text="(.*?)">(.*?)</requirement>', text, re.S):
            hits = [(cid, float(sc), title) for cid, sc, title in re.findall(r"\[(.+?)\] \(score ([\d.]+)\) (.+)", evidence)]
            ids = [cid for cid, sc, _ in hits if sc >= 1 and cid not in ("top", "about")][:2]
            title = next((t for cid, _, t in hits if ids and cid == ids[0]), "")
            items.append(
                RelevantWork(
                    requirement=req,
                    covered=bool(ids),
                    evidence=f"See {title}." if ids else "Not shown in the portfolio.",
                    citations=ids,
                )
            )
        covered = sum(i.covered for i in items)
        return RelevanceReport(
            summary=f"Demo mode matched by keywords only: {covered} of {len(items)} requirements point to work in the portfolio. "
            "Add an API key for a real read.",
            items=items,
        )

    def _EmailDraft(self, text):
        convo = _between(text, "conversation")
        last = convo.strip().splitlines()[-1] if convo.strip() else ""
        last = re.sub(r"^visitor:\s*", "", last, flags=re.I)
        return EmailDraft(
            subject="Hello from your portfolio",
            body=f"Hi Taniksha,\n\nI came across your portfolio and wanted to reach out. {last}\n\n"
            "Would you be open to a quick chat?\n\nBest,\n[Your name]",
        )


class DemoLLM:
    def with_structured_output(self, schema, **_):
        return _Structured(schema)

    async def astream(self, messages):
        text = _last_human(messages)
        context = _between(text, "context")
        first = re.search(r"\[(.+?)\] (.+?)\n(.+?)(?:\n|$)", context)
        if first:
            cid, title, body = first.groups()
            sentence = re.split(r"(?<=[.!?])\s", body.strip())[0]
            reply = (
                f"Demo mode (no API key), so this is the top retrieved passage rather than a written answer. "
                f"From {title}: {sentence} [{cid}]"
            )
        else:
            reply = "I don't have anything in the portfolio that answers that. You could ask Taniksha directly by email."
        for word in re.findall(r"\S+\s*", reply):
            await asyncio.sleep(0.02)
            yield SimpleNamespace(content=word)
