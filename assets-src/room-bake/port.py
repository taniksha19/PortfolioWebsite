# Convert the published artifact (desk-3d.html) into React-site modules:
#   src/fun/room.js   -> export async function mountRoom(root, opts) returning dispose()
#   src/fun/room.css  -> the room's styles, scoped under .fun-root
# usage: python -I port.py desk-3d.html askagent.js outdir
import re, sys, os
SRC, ASK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(SRC, encoding="utf-8").read()
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ JS
js = s[s.index('<script type="module">') + len('<script type="module">'):]
js = js[:js.index("</script>")]
def R(a, b, count=1):
    global js
    assert a in js, "MISSING: " + a[:100]
    js = js.replace(a, b, count)
def cut(start, end_marker, repl):
    global js
    i = js.index(start); j = js.index(end_marker, i) + len(end_marker)
    js = js[:i] + repl + js[j:]

lines = js.strip("\n").split("\n")
imports = [l for l in lines if l.startswith("import ")]
body = "\n".join(l for l in lines if not l.startswith("import "))
js = body

cut("const D = {", "\n};\n", "const D = data;\n")
cut("const KIT_GLB = {", "\n};\n", 'const KIT_NAMES = ["pottedPlant", "plantSmall1", "plantSmall2", "plantSmall3", "bookcaseOpenLow", "books", "computerMouse", "radio"];\nlet kitFailed = false;\n')
cut("await Promise.all(Object.entries(KIT_GLB)", "})));",
    'await Promise.all(KIT_NAMES.map((k) => gltfLoader.loadAsync(assetBase + "desk/models/" + k + ".glb").then((g) => { kitSrc[k] = g.scene; }).catch(() => { kitFailed = true; })));')
js = re.sub(r'const avatarURL = "data:[^"]*";', 'const avatarURL = assetBase + "taniksha.png";', js, count=1)
js = re.sub(r'const BAKED_GLB = "[^"]*";\n', "", js, count=1)
R('new Promise((res, rej) => gltfLoader.parse(Uint8Array.from(atob(BAKED_GLB), (c) => c.charCodeAt(0)).buffer, "", res, rej))', 'gltfLoader.loadAsync(assetBase + "desk/baked.glb")')
R('loadT("lm-day.jpg"), loadT("lm-night.jpg")', 'loadT(assetBase + "desk/lm-day.jpg"), loadT(assetBase + "desk/lm-night.jpg")')
# a kit model that failed to load would shift the mesh order the bake was matched against
R('  if (location.search.includes("export") || location.search.includes("nobake")) return 0;',
  '  if (kitFailed || location.search.includes("export") || location.search.includes("nobake")) return 0;')
# résumé: a normal download on the real site
cut("/* résumé download", "\n}\n", '/* résumé download */\nfunction getResume() { const a = document.createElement("a"); a.href = data.resume; a.download = "Taniksha-Datar-Resume.pdf"; document.body.appendChild(a); a.click(); a.remove(); }\n')
# mode toggle leaves the room
R('$("#mode-simple").onclick = () => toast("Simple mode is your current scrolling portfolio. This prototype only shows the room.");', '$("#mode-simple").onclick = () => onExit();')
# DOM lookups stay inside this room
R("const $ = (s) => document.querySelector(s);", "const $ = (s) => root.querySelector(s);")
# every listener is tracked so unmounting removes it
js = re.sub(r"(?<![\w.])(\w+)\.addEventListener\(", r"on(\1, ", js)
js = re.sub(r"(?m)^addEventListener\(", "on(window, ", js)
R("new ResizeObserver(resize).observe(stage);", "const ro = new ResizeObserver(resize); ro.observe(stage); cleanups.push(() => ro.disconnect());")
js = js.replace("requestAnimationFrame(frame);", "raf = requestAnimationFrame(frame);")
R("function frame(now) {", "function frame(now) {\n  if (disposed) return;")
js = js.replace("document.querySelectorAll(", "root.querySelectorAll(").replace("document.querySelector(", "root.querySelector(")
# project cards link to their code
R("${chips(p.st)}${p.game ?", '${chips(p.st)}${p.link ? `<p style="margin-top:12px"><a class="btn ghost" href="${esc(p.link)}" target="_blank" rel="noopener">View the code</a></p>` : ""}${p.game ?')
# Nimbus: the real agent
R('setTimeout(() => { const t = log.querySelector(".typing"); t.classList.remove("typing"); t.textContent = nimbusAnswer(q); blip(1450, .06, .03); }, 650); };',
  'askAgent(q, log.querySelector(".typing")).then(() => blip(1450, .06, .03)); };')
R("Prototype: these answers come from her portfolio. On the live site, Nimbus is her LangGraph agent.", "I'm Taniksha's LangGraph agent. If my server is napping, I answer from her portfolio instead.")
R(" On her live site I'm connected to her full agent.", "")
R("function nimbusAnswer(q) {", open(ASK, encoding="utf-8").read() + "function nimbusAnswer(q) {")

head = "\n".join(imports) + """

/* The fun-mode room: a three.js scene with Blender-baked lighting, mounted into `root`
   (the .fun-root element rendered by FunMode.jsx). Returns a dispose() function.
   Static meshes are named bk_N in build order and matched to public/desk/baked.glb,
   so changing what gets built means re-running the bake (assets-src/room-bake). */
export async function mountRoom(root, { data, onExit, agentUrl, base: assetBase = "/" }) {
let disposed = false, raf = 0;
const cleanups = [];
const on = (target, type, fn, opts) => { target.addEventListener(type, fn, opts); cleanups.push(() => target.removeEventListener(type, fn, opts)); };
"""
tail = """
return () => {
  disposed = true; cancelAnimationFrame(raf);
  cleanups.forEach((f) => f());
  try { if (snd.ctx) snd.ctx.close(); } catch { /* already closed */ }
  composer.dispose?.(); renderer.dispose(); renderer.forceContextLoss(); renderer.domElement.remove();
};
}
"""
open(os.path.join(OUT, "room.js"), "w", encoding="utf-8").write("/* eslint-disable */\n" + head + js.strip("\n") + "\n" + tail)

# ------------------------------------------------------------------ CSS, scoped under .fun-root
css = s[s.index("<style>") + 7: s.index("</style>")]
css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
def scope_sel(sel):
    sel = sel.strip()
    if sel == ":root": return ".fun-root"
    if sel.startswith(":root"): return sel + " .fun-root"
    if sel == "body": return ".fun-root"
    if sel == "*": return ".fun-root, .fun-root *"
    return ".fun-root " + sel
def scope_prelude(p):
    p = p.strip()
    if re.fullmatch(r"html,\s*body", p): return "html.fun-open, html.fun-open body"
    return ", ".join(scope_sel(x) for x in p.split(","))
out, i, n = [], 0, len(css)
def block_end(k):
    d = 0
    while k < n:
        if css[k] == "{": d += 1
        elif css[k] == "}":
            d -= 1
            if d == 0: return k
        k += 1
    raise ValueError("unbalanced")
def walk(lo, hi, inner):
    k = lo
    while k < hi:
        b = css.find("{", k, hi)
        if b < 0: break
        prelude = css[k:b].strip(); e = block_end(b)
        if prelude.startswith("@keyframes"): inner.append(prelude + " " + css[b:e + 1])
        elif prelude.startswith("@media") or prelude.startswith("@supports"):
            sub = []; walk(b + 1, e, sub); inner.append(prelude + " {\n  " + "\n  ".join(sub) + "\n}")
        else: inner.append(scope_prelude(prelude) + " " + css[b:e + 1].strip())
        k = e + 1
walk(0, n, out)
fixes = """
/* the room is the whole viewport while it is open */
.fun-root { position: fixed; inset: 0; z-index: 60; overflow: hidden; }
/* undo the site's CSS reset where the room's views rely on browser defaults */
.fun-root h3 { font-size: 1.17em; font-weight: 700; margin: 0; line-height: 1.25; }
.fun-root p { margin: 0 0 .7em; }
.fun-root ul.pts { list-style: disc; padding-left: 1.2em; margin: .5em 0; }
.fun-root ul.pts li { margin: .25em 0; }
"""
open(os.path.join(OUT, "room.css"), "w", encoding="utf-8").write("/* Fun-mode room styles, scoped under .fun-root (ported from the prototype). */\n" + "\n".join(out) + "\n" + fixes)
print("ok", len(js), "js chars;", len(out), "css rules")
