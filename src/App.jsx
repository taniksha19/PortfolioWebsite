import { Nav } from "./components/Nav";
import { DreamyBackground } from "./components/DreamyBackground";
import { Hero } from "./components/Hero";
import { Experience } from "./components/Experience";
import { Projects } from "./components/Projects";
import { Skills } from "./components/Skills";
import { AgentSection } from "./components/agent/AgentSection";
import { Contact } from "./components/Contact";
import { profile } from "./data";

export default function App() {
  return (
    <>
      <DreamyBackground />
      <div className="grain" aria-hidden="true" />
      <Nav />
      <main>
        <Hero />
        <Experience />
        <Projects />
        <AgentSection />
        <Skills />
        <Contact />
      </main>
      <footer className="mx-auto flex max-w-6xl flex-wrap justify-between gap-2 border-t border-line px-4 py-8 font-mono text-xs text-muted sm:px-6">
        <span>© {new Date().getFullYear()} {profile.name}</span>
        <span>React · LangGraph · FastAPI</span>
      </footer>
    </>
  );
}
