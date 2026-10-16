// Live diagram of the LangGraph agent. Mirrors backend/app/graph.py.

const W = 96;
const H = 34;

const NODES = {
  router: { x: 212, y: 36, label: "Router" },
  retriever: { x: 56, y: 126, label: "Retriever" },
  extractor: { x: 160, y: 126, label: "Req. extractor" },
  contact_drafter: { x: 264, y: 126, label: "Contact drafter" },
  guardrail: { x: 368, y: 126, label: "Guardrail" },
  answerer: { x: 56, y: 216, label: "Answerer" },
  matcher: { x: 160, y: 216, label: "Work matcher" },
  citation_check: { x: 108, y: 306, label: "Citation check" },
  response: { x: 212, y: 396, label: "Response" },
};

const EDGES = [
  ["router", "retriever"],
  ["router", "extractor"],
  ["router", "contact_drafter"],
  ["router", "guardrail"],
  ["retriever", "answerer"],
  ["extractor", "matcher"],
  ["answerer", "citation_check"],
  ["matcher", "citation_check"],
  ["citation_check", "response"],
  ["contact_drafter", "response"],
  ["guardrail", "response"],
];

function edgePath(a, b) {
  const x1 = a.x;
  const y1 = a.y + H / 2;
  const x2 = b.x;
  const y2 = b.y - H / 2;
  const my = (y1 + y2) / 2;
  return `M${x1},${y1} C${x1},${my} ${x2},${my} ${x2},${y2}`;
}

export function AgentGraph({ nodes, run }) {
  const finished = run.state === "finished";
  const status = (id) => {
    if (id === "response") return finished && Object.keys(nodes).length ? "done" : "idle";
    return nodes[id] || (finished ? "skipped" : "idle");
  };

  return (
    <svg viewBox="0 0 424 424" className="agent-graph w-full" role="img" aria-label="Agent graph: router, specialist agents, citation check">
      <defs>
        <marker id="arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0,0 L8,4 L0,8 z" fill="var(--line)" />
        </marker>
        <marker id="arrow-on" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0,0 L8,4 L0,8 z" fill="var(--accent)" />
        </marker>
      </defs>

      {EDGES.map(([from, to]) => {
        const on = status(from) === "done" && ["active", "done"].includes(status(to));
        return (
          <path
            key={`${from}-${to}`}
            d={edgePath(NODES[from], NODES[to])}
            className={`edge ${on ? "edge-on" : ""} ${finished && !on ? "edge-dim" : ""}`}
            markerEnd={`url(#${on ? "arrow-on" : "arrow"})`}
          />
        );
      })}

      {Object.entries(NODES).map(([id, n]) => {
        const s = status(id);
        return (
          <g key={id} className={`node node-${s}`} transform={`translate(${n.x - W / 2}, ${n.y - H / 2})`}>
            <rect width={W} height={H} rx={9} />
            <text x={W / 2} y={H / 2 + 4} textAnchor="middle">
              {n.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
