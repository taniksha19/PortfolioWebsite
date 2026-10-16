---
target: agent
---

# How this agent works

## Overview
Nimbus is the agent on this portfolio. It answers questions about Taniksha's work, projects, skills, education and interests, using only the content on this site. It is a LangGraph state graph served by a FastAPI backend, and every step it takes streams to the page, which is what lights up the graph and fills the trace next to the chat.

## Architecture
A router reads each message and classifies it (with structured output) as a question, a role to match against, a request to get in touch, or something off-topic. Questions go to a retriever and then an answerer. Roles go to a requirement extractor and then a work matcher. Contact requests go to an email drafter. Off-topic messages go to a guardrail that politely declines. Answers and role matches finish with a deterministic citation check before anything is shown.

## Retrieval
The retriever uses BM25 over small chunks of the same content file that renders this website, plus longer project write-ups. BM25 fits here because the corpus is small, technical terms like LoRA, MCP or Viterbi need exact matches, and it is deterministic, free and adds no embedding latency. Vague questions such as "where is she from?" fall back to the profile chunks instead of returning nothing. Every chunk id maps to a section of the page, which is why clicking a citation scrolls to it.

## Grounding and citations
The answerer may only use the retrieved context and must cite a chunk id after each claim. The citation check then removes any citation that does not point at retrieved context, and in role matches it marks a requirement as not shown when no valid evidence is left. When the portfolio does not answer a question, Nimbus says so and suggests emailing Taniksha instead of guessing.

## Why it points to work instead of scoring fit
An agent built by the candidate should not grade the candidate, and nobody should trust it if it did. So when a role is pasted, Nimbus extracts the requirements and points to the parts of the portfolio that are relevant to each one, with citations, and lists what the portfolio does not show. It is a navigation aid for a busy reader, not a hiring verdict.

## Testing
A pytest suite runs on every change. It includes a retrieval regression set, where each question must retrieve the expected chunk in the top results; end-to-end runs of every graph path in a keyless demo mode; a unit test for the citation check; an HTTP streaming test; and input validation tests.

## Streaming and interface
The backend streams Server-Sent Events: a start and finish event for every node with its timing and a short detail, tokens as the answer is written, and a final structured result. The React frontend uses those events to animate the graph, show the trace, render citations as chips and highlight the cited sections on the page.

## Model, cost and safety controls
The language model is called through OpenRouter (Gemini 2.5 Flash by default) and can be switched to Google or Groq with one setting. Output length is capped, there are per-visitor and daily rate limits, message length is limited, and the API key stays on the server. Without a key the backend runs a rule-based demo mode so the whole graph still works.

## Tech stack
Python, LangGraph, LangChain, FastAPI and rank-bm25 on the backend; React, Vite, Tailwind CSS and Framer Motion on the frontend.
