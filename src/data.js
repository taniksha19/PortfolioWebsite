// All site content lives in content/portfolio.json, shared with the agent backend.
// Edit that file to update both the site and what the agent knows.
import content from "../content/portfolio.json";

export const { profile, about, experience, projects, skills, education } = content;

// Base URL of the agent API. In production render.yaml fills VITE_AGENT_URL from the API service;
// a bare hostname is accepted too and gets https:// added.
const agentUrl = (import.meta.env.VITE_AGENT_URL || "http://localhost:8000").trim().replace(/\/$/, "");
export const AGENT_URL = /^https?:\/\//.test(agentUrl) ? agentUrl : `https://${agentUrl}`;
