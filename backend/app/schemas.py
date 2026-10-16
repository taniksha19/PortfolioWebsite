"""Structured outputs the agents produce."""

from typing import Literal

from pydantic import BaseModel, Field

Intent = Literal["question", "job_fit", "contact", "off_topic"]


class Route(BaseModel):
    intent: Intent = Field(
        description=(
            "question: asks about Taniksha (background, story, interests and hobbies, skills, work, projects, education), "
            "or about you, this assistant (Nimbus), and how this site or agent was built. "
            "job_fit: the message is or contains a job description or list of requirements, or asks which work is relevant to a role. "
            "contact: wants to reach out, hire, schedule or email Taniksha. "
            "off_topic: anything unrelated to Taniksha (general trivia, coding help, other people)."
        )
    )
    reason: str = Field(description="One short sentence explaining the choice.")


class Requirements(BaseModel):
    role_title: str = Field(description="Job title from the description, or 'the role' if none is given.")
    requirements: list[str] = Field(description="Up to 8 concrete, distinct requirements, each under 12 words.")


class RelevantWork(BaseModel):
    requirement: str
    covered: bool = Field(description="True if the portfolio shows evidence for this requirement.")
    evidence: str = Field(description="One sentence naming where in the portfolio this shows up, or 'Not shown in the portfolio.'")
    citations: list[str] = Field(description="Chunk ids that show this requirement. Empty when not covered.")


class RelevanceReport(BaseModel):
    summary: str = Field(
        description="One or two sentences telling the reader which parts of the portfolio to look at first for this role. "
        "No judgement of fit or hireability."
    )
    items: list[RelevantWork]


class EmailDraft(BaseModel):
    subject: str
    body: str = Field(description="A short, friendly email to Taniksha from the visitor, under 120 words, signed '[Your name]'.")
