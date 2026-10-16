export const SAMPLE_JD = `AI Engineer, Applied LLMs
Requirements:
- Build and ship RAG systems and LLM agents to production
- Strong Python; experience with FastAPI or similar
- Evaluation of LLM outputs and regression testing
- Cloud deployment on GCP or AWS with Docker and CI/CD
- Experience with Kubernetes
- Familiarity with LangChain or LangGraph`;

// Shown in the hero console and as one-click prompts in the agent section.
const ANSWER = ["router", "retriever", "answerer", "citation_check"];
export const DEMO_PROMPTS = [
  { label: "Give me the 30-second version of Taniksha", path: ANSWER },
  { label: "How were you built?", path: ANSWER },
  { label: "Walk me through Break The Bot's pipeline", path: ANSWER },
  { label: "Explain the Bevi work without jargon", path: ANSWER },
  { label: "Which work is relevant to an AI Engineer role?", message: SAMPLE_JD, path: ["router", "extractor", "matcher", "citation_check"] },
];

// Offered as "Ask next" once the starter prompts have been used. Every one is answerable from the site.
export const MORE_PROMPTS = [
  { label: "Tell me about the multilingual detox project" },
  { label: "How does your citation check work?" },
  { label: "What did Taniksha study, and where?" },
  { label: "Which tools does Taniksha use most?" },
  { label: "What does Taniksha do for fun?" },
  { label: "Draft an intro email to Taniksha" },
];

// Lets any part of the page hand a prompt to the agent section.
export function askAgent(prompt) {
  document.getElementById("agent")?.scrollIntoView({ behavior: "smooth", block: "start" });
  window.dispatchEvent(new CustomEvent("agent:ask", { detail: prompt.message || prompt.label }));
}
