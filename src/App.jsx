import { Suspense, lazy, useCallback, useState } from "react";
import { Nav } from "./components/Nav";
import { DreamyBackground } from "./components/DreamyBackground";
import { Hero } from "./components/Hero";
import { Experience } from "./components/Experience";
import { Projects } from "./components/Projects";
import { Skills } from "./components/Skills";
import { AgentSection } from "./components/agent/AgentSection";
import { Contact } from "./components/Contact";
import { RoomPeek } from "./components/RoomPeek";
import { profile } from "./data";

// Fun mode (the 3D room) is its own chunk: three.js only downloads when someone switches to it.
const FunMode = lazy(() => import("./fun/FunMode"));

const funInUrl = () => new URLSearchParams(window.location.search).has("fun");
function setFunInUrl(on) {
  const url = new URL(window.location.href);
  if (on) url.searchParams.set("fun", "");
  else url.searchParams.delete("fun");
  window.history.replaceState(null, "", url.toString().replace("?fun=", "?fun").replace("&fun=", "&fun"));
}

export default function App() {
  const [fun, setFun] = useState(funInUrl);
  const enterFun = useCallback(() => {
    setFunInUrl(true);
    setFun(true);
  }, []);
  const exitFun = useCallback(() => {
    setFunInUrl(false);
    setFun(false);
  }, []);

  return (
    <>
      {/* The simple site stays mounted while the room is open, so scroll position and chats survive. */}
      <div hidden={fun}>
        <DreamyBackground />
        <div className="grain" aria-hidden="true" />
        <Nav onFun={enterFun} />
        <main>
          <Hero />
          <Experience />
          <Projects />
          <AgentSection />
          <Skills />
          <RoomPeek onFun={enterFun} />
          <Contact />
        </main>
        <footer className="mx-auto flex max-w-6xl flex-wrap justify-between gap-2 border-t border-line px-4 py-8 font-mono text-xs text-muted sm:px-6">
          <span>© {new Date().getFullYear()} {profile.name}</span>
          <span>React · LangGraph · FastAPI · three.js</span>
        </footer>
      </div>
      {fun && (
        <Suspense fallback={<div className="fun-loading">setting up the room…</div>}>
          <FunMode onExit={exitFun} />
        </Suspense>
      )}
    </>
  );
}
