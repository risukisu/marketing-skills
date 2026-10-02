"""A small flat diagram loop for the renderer tests: white ground, three boxes joined by
thin connectors, small labels, one accent. Choreographed: beat i lights box i, holds, and
resets. One dotted connector marches the whole time so the typical step is not zero.

`page_html(reset=(start, end))` sets the window of `q` over which the lit box fades back to
rest. The box fades in over `q` 0 to 0.15. A reset that ends by the beat's last sampled frame,
(F-1)/F with F frames per beat, is a fade; (0.95, 1.0) is the too-short reset that is still
lit on the last frame and snaps at the beat boundary.
"""

W, H = 400, 240
BEATS = 3
ACCENT = "#3fd68c"

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html, body { margin: 0; width: %(w)dpx; height: %(h)dpx; overflow: hidden; background: #ffffff; }
svg { display: block; }
</style></head><body>
<svg width="%(w)d" height="%(h)d" viewBox="0 0 %(w)d %(h)d" xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif">
  <g id="boxes"></g>
  <line x1="120" y1="120" x2="150" y2="120" stroke="#9a9a9a" stroke-width="1"/>
  <line x1="250" y1="120" x2="280" y2="120" stroke="#9a9a9a" stroke-width="1"/>
  <line id="march" x1="20" y1="200" x2="380" y2="200" stroke="#9a9a9a" stroke-width="2" stroke-dasharray="2 8"/>
  <text x="20" y="30" font-size="11" fill="#333">three steps, one accent</text>
</svg>
<script>
const BEATS = %(beats)d, RESET0 = %(r0)s, RESET1 = %(r1)s, ACCENT = "%(accent)s", REST = "#dddddd";
const g = document.getElementById("boxes");
const boxes = [];
for (let i = 0; i < BEATS; i++) {
  const r = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  r.setAttribute("x", 20 + i * 130); r.setAttribute("y", 90);
  r.setAttribute("width", 100); r.setAttribute("height", 60);
  r.setAttribute("fill", REST);
  g.appendChild(r); boxes.push(r);
}
function mix(a, b, t) {
  const pa = [1, 3, 5].map(k => parseInt(a.slice(k, k + 2), 16));
  const pb = [1, 3, 5].map(k => parseInt(b.slice(k, k + 2), 16));
  return "rgb(" + pa.map((v, k) => Math.round(v + (pb[k] - v) * t)).join(",") + ")";
}
function setPhase(p) {
  const beat = Math.floor(p * BEATS), q = p * BEATS - beat;
  for (let i = 0; i < BEATS; i++) {
    let lit = 0;
    if (i === beat) {
      lit = Math.min(1, q / 0.15);                                  // fade in over 0.15 of q (three frames at F = 20)
      if (q >= RESET0) lit = Math.max(0, 1 - (q - RESET0) / (RESET1 - RESET0));  // reset
    }
    boxes[i].setAttribute("fill", mix(REST, ACCENT, lit));
  }
  document.getElementById("march").setAttribute("stroke-dashoffset", (-p * 10).toFixed(3));
}
window.setPhase = setPhase;
setPhase(0);
</script></body></html>"""


def page_html(reset=(0.6, 0.9)):
    return PAGE % dict(w=W, h=H, beats=BEATS, r0=reset[0], r1=reset[1], accent=ACCENT)
