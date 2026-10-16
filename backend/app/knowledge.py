"""Portfolio knowledge base: turns content/portfolio.json and the write-ups in content/notes/
into citable chunks and a BM25 retriever.

The corpus is small (a few dozen chunks), so lexical BM25 is accurate, free, deterministic and
needs no embedding API. Every chunk id maps to a DOM id on the site (write-up chunks are
"<section-id>--<heading>"), so citations can link straight to where they came from.
"""

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from rank_bm25 import BM25Okapi

CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"
CONTENT_PATH = CONTENT_DIR / "portfolio.json"
NOTES_DIR = CONTENT_DIR / "notes"

STOPWORDS = set(
    "a an and are as at be by did do does for from has have her his how i in is it its me my of on "
    "or she that the their them they this to was what when where which who why with you your "
    "taniksha datar tell about any ever".split()
)


@dataclass(frozen=True)
class Chunk:
    id: str
    title: str
    text: str


IRREGULAR = {"built": "build", "building": "build", "ran": "run", "wrote": "write", "written": "write"}


def _stem(t: str) -> str:
    t = IRREGULAR.get(t, t)
    if len(t) > 4 and t.endswith("s") and not t.endswith("ss"):
        t = t[:-1]
    return t


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9+#]+(?:\.[a-z0-9]+)*", text.lower().replace("-", " "))
    return [_stem(t) for t in words if t not in STOPWORDS]


def build_chunks(content: dict) -> list[Chunk]:
    p = content["profile"]
    chunks = [
        Chunk(
            id="top",
            title="About Taniksha",
            text=(
                f"{p['name']} is an {p['role']} focused on {', '.join(p['focus'])}, based in {p['location']}. "
                f"{p['intro']} Contact: {p['email']}. LinkedIn: {p['linkedin']}. GitHub: {p['github']}."
            ),
        )
    ]
    if ab := content.get("about"):
        chunks.append(
            Chunk(
                id=ab["id"],
                title="About Taniksha: background and interests",
                text=f"{ab['intro']} " + " ".join(f"{f}." for f in ab["firsts"]) + " Interests and hobbies: "
                + " ".join(f"{i['title']}: {i['text']} ({i.get('keywords', '')})" for i in ab["interests"])
                + f" Keywords: {ab.get('keywords', '')}.",
            )
        )
    for e in content["experience"]:
        chunks.append(
            Chunk(
                id=e["id"],
                title=f"{e['role']} at {e['company']}",
                text=f"{e['role']} at {e['company']} ({e['period']}, {e['location']}). "
                + " ".join(e["points"])
                + f" Tools: {', '.join(e['tags'])}.",
            )
        )
    for pr in content["projects"]:
        chunks.append(
            Chunk(
                id=pr["id"],
                title=f"Project: {pr['title']}",
                text=f"Project {pr['title']} ({pr['kind']}). {pr['summary']} "
                + " ".join(pr["points"])
                + f" Stack: {', '.join(pr['stack'])}.",
            )
        )
    for s in content["skills"]:
        chunks.append(Chunk(id=s["id"], title=f"Skills: {s['group']}", text=f"{s['group']} skills: {', '.join(s['items'])}."))
    for ed in content["education"]:
        chunks.append(
            Chunk(
                id=ed["id"],
                title=f"Education: {ed['school']}",
                text=f"{ed['degree']} at {ed['school']} ({ed['period']}, {ed['location']}). {ed['detail']}.",
            )
        )
    return chunks


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def parse_note(raw: str) -> tuple[dict, str, list[tuple[str, str]]]:
    """Split a write-up into (frontmatter, title, [(heading, body)])."""
    meta: dict = {}
    if raw.startswith("---"):
        _, front, raw = raw.split("---", 2)
        for line in front.strip().splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    title_match = re.search(r"^# (.+)$", raw, re.M)
    title = title_match.group(1).strip() if title_match else meta.get("target", "Notes")
    sections = [
        (block.split("\n", 1)[0].strip(), block.split("\n", 1)[1].strip() if "\n" in block else "")
        for block in re.split(r"^## ", raw, flags=re.M)[1:]
    ]
    return meta, title, sections


def note_chunks(notes_dir: Path = NOTES_DIR) -> list[Chunk]:
    """One chunk per "## " section. Sections still marked TODO are skipped, so placeholders never
    reach the agent."""
    chunks = []
    for path in sorted(notes_dir.glob("*.md")):
        meta, title, sections = parse_note(path.read_text(encoding="utf-8"))
        target = meta.get("target") or path.stem
        # A team project's attribution travels with every section, so it's there whichever one is retrieved.
        team = next((" ".join(body.split()) for heading, body in sections if heading.lower() == "team"), "")
        for heading, body in sections:
            if not body or body.strip().upper().startswith("TODO"):
                continue
            text = " ".join(body.split())
            if team and heading.lower() != "team":
                text += f" (Team project: {team})"
            chunks.append(Chunk(id=f"{target}--{_slug(heading)}", title=f"{title}: {heading}", text=text))
    return chunks


class Retriever:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.by_id = {c.id: c for c in chunks}
        self._bm25 = BM25Okapi(b=0.4, corpus=[tokenize(f"{c.title} {c.title} {c.text}") for c in chunks])

    # General profile chunks, used when a question is too vague to match anything ("where is she from?").
    FALLBACK_IDS = ("top", "about")

    def search(self, query: str, k: int = 4) -> list[tuple[Chunk, float]]:
        tokens = tokenize(query)
        hits = []
        if tokens:
            scores = self._bm25.get_scores(tokens)
            ranked = sorted(zip(self.chunks, scores), key=lambda pair: pair[1], reverse=True)
            hits = [(c, float(s)) for c, s in ranked[:k] if s > 0]
        return hits or [(self.by_id[i], 0.0) for i in self.FALLBACK_IDS if i in self.by_id]


@lru_cache
def load_content() -> dict:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


@lru_cache
def get_retriever() -> Retriever:
    return Retriever(build_chunks(load_content()) + note_chunks())
