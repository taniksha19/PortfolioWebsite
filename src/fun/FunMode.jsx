import { useEffect, useRef, useState } from "react";
import "./room.css";
import { mountRoom } from "./room";
import { roomData } from "./roomData";
import { AGENT_URL } from "../data";

// Fun mode: a full-screen 3D room. Loaded lazily, so three.js only downloads when someone opens it.
export default function FunMode({ onExit }) {
  const ref = useRef(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let dispose = null;
    let cancelled = false;
    document.documentElement.classList.add("fun-open");
    // Deferred one tick so React StrictMode's mount/unmount/mount in dev never starts two scenes.
    const t = setTimeout(() => {
      mountRoom(ref.current, { data: roomData, onExit, agentUrl: AGENT_URL, base: import.meta.env.BASE_URL })
        .then((d) => (cancelled ? d() : (dispose = d)))
        .catch(() => !cancelled && setFailed(true));
    }, 0);
    return () => {
      cancelled = true;
      clearTimeout(t);
      if (dispose) dispose();
      document.documentElement.classList.remove("fun-open");
    };
  }, [onExit]);

  return (
    <div className="fun-root" ref={ref}>
      <div className="wrap">
        <div className="bar">
          <div className="brand">
            Taniksha Datar <span>· AI Engineer</span>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <button className="snd" id="labels" aria-pressed="false">
              Labels off
            </button>
            <button className="snd" id="sound" aria-pressed="false">
              ♪ Sound off
            </button>
            <div className="toggle" role="group" aria-label="Portfolio mode">
              <button id="mode-simple" aria-pressed="false" onClick={failed ? onExit : undefined}>
                Simple
              </button>
              <button id="mode-fun" aria-pressed="true">
                Make it fun ✨
              </button>
            </div>
          </div>
        </div>
        <div className="stage" id="stage">
          <div className="loading" id="loading">
            {failed ? "This browser can't show the 3D room. The simple portfolio works everywhere." : "setting up the room…"}
          </div>
          <div className="bubble hide" id="bubble" aria-live="polite" />
          <div className="whisper" id="whisper" />
          <div className="hint" id="hint">
            Click anything in the room · the lamp switches to night
          </div>
        </div>
      </div>

      <div className="view" id="view" hidden role="dialog" aria-modal="true" aria-label="Section">
        <div className="view-inner">
          <button className="back" id="back">
            ← Back to the desk
          </button>
          <div id="view-body" />
        </div>
      </div>
      <div className="toast" id="toast" hidden />
    </div>
  );
}
