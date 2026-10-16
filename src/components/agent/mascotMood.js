export const MASCOT_NAME = "Nimbus";

const LINES = {
  sleepy: "zzz… waking up the server, one sec",
  offline: "I’m napping right now. Email Taniksha instead?",
  idle: "Hi! Ask me anything about Taniksha’s work.",
  thinking: "Hmm, let me look through the portfolio…",
  talking: "Here’s what I found…",
  answered: "Anything else you’d like to know?",
  happy: "Found plenty of relevant work for this role!",
  mixed: "Here’s where to look, plus what the portfolio doesn’t show.",
  unsure: "I couldn’t back that up from the portfolio. Maybe email Taniksha?",
  email: "Drafted! Hit “Open in email app” to send it.",
};

const UNSURE = /don['’]t know|couldn['’]t find|don['’]t have|nothing in the portfolio|i can only talk/i;

// Maps the agent's state to a mascot mood plus the line it says. `settled` = the post-answer
// reaction has played, so fall back to idle.
export function mascotState({ health, run, messages, nodes, settled }) {
  if (health.status === "checking" || health.status === "waking") return { mood: "sleepy", line: LINES.sleepy };
  if (health.status === "offline") return { mood: "sleepy", line: LINES.offline };

  const last = messages[messages.length - 1];
  if (run.state === "running") {
    const talking = nodes.answerer === "active" && last?.text;
    return talking ? { mood: "talking", line: LINES.talking } : { mood: "thinking", line: LINES.thinking };
  }
  if (!last || last.role !== "assistant") return { mood: "idle", line: LINES.idle };

  let reaction = { mood: "idle", line: LINES.answered };
  if (last.kind === "error") reaction = { mood: "unsure", line: last.text };
  else if (last.kind === "email") reaction = { mood: "happy", line: LINES.email };
  else if (last.kind === "relevance") {
    const covered = last.items.filter((i) => i.covered).length;
    if (covered >= last.items.length / 2) reaction = { mood: "happy", line: LINES.happy };
    else reaction = { mood: "idle", line: LINES.mixed };
  } else if (UNSURE.test(last.text || "")) reaction = { mood: "unsure", line: LINES.unsure };

  return settled ? { mood: "idle", line: reaction.line } : reaction;
}
