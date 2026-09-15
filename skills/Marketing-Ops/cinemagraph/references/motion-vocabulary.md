# Motion vocabulary

Every motion is a pure function of the phase `p` in [0, 1). State at `p = 1` equals state at `p = 0`, so the loop closes regardless of frame count. Amplitudes below are starting points for "subtle"; halve them before you double them.

`sin(p)` below means `Math.sin(2 * Math.PI * p)`, which is periodic in p by construction.

## Light-mode motions (move what already exists)

| Motion | Formula | Says | Wrong when |
|---|---|---|---|
| **March** | `stroke-dashoffset = -p × period` on a dashed/dotted stroke; `period` = dash + gap | Continuation, "keeps going", flow direction | The dots are data points, not a leader line |
| **Pulse** | ring `r = r0 + p × Δr`, `opacity = a0 × (1 − p)`; add a second ring at `(p + 0.5) mod 1` for continuity | "This point matters", a live state, a decision moment | Applied to more than one point; two pulses fight |
| **Drift** | `translate(p × period)` on a `<pattern>` inner group or clipped texture copy | Ongoing cost, accumulation, background process | The texture has a visible edge that is not masked |
| **Blink** | `opacity = p mod 1 < duty ? 1 : 0` with duty ≈ 0.55; or a soft `0.5 + 0.5 × sin(p)` | A cursor, "recording", an LED | More than one blinker in view |
| **Breathe** | `scale = 1 + 0.05 × sin(p)` or `opacity = 0.8 + 0.2 × sin(p)` on a glow or node | Alive, idle, waiting | Applied to text or anything with edges the eye tracks |
| **Flow** | move a gradient stop: `offset = p`, with the gradient repeating; or slide a highlight rectangle along a clipped edge | Data moving along a pipe, energy, a link being used | The line is short; the highlight then looks like a bug |
| **Sway** | `rotate(1.5 × sin(p), pivot)` on a hanging or leaf-like element | A gentle environment (photos, illustrations) | Anything mechanical or diagrammatic |
| **Shimmer** | a soft diagonal white band with `opacity 0.08`, `translate(p × width)` clipped to a card | Glass, polish, "new" | On a chart or anything with text under the band |

Combine at most three, at different frequencies. Two motions at the same period side by side read as a rendering glitch.

## Heavy-mode motions (add elements, keep ~95%)

| Motion | Formula | Says | Guardrail |
|---|---|---|---|
| **Scan** | a 2–6 px line or a faint band sweeps across a region, `x = x0 + p × width`; fade in/out in the first/last 10% of p | Inspection, checking, monitoring | Never let it cross text at full opacity; drop to 0.2 over labels |
| **Draw** | `stroke-dasharray = L; stroke-dashoffset = L × (1 − ease(p))`, where `L` is the path length; hold fully drawn for the last 20–30% of p, then snap | A path being traced, a route, a signature | Snap-back must land on a frame where the path is already invisible or already complete; otherwise the loop pops |
| **Particles** | N dots with fixed random seeds: `y = y0 − ((p + seed) mod 1) × height`, `opacity` peaks mid-travel | Activity, throughput, uplift | Seeds fixed at author time, never `Math.random()` at render time |
| **Counter** | text `value = floor(start + ((p + 0.1) mod 1) × range)` with a hold at the end | A metric climbing | Use tabular figures so width does not jitter; loop wrap is visible, so keep the range small or place it where a reset reads naturally |
| **Typewriter** | reveal `floor(p × N)` characters, hold, clear | A prompt, a command | The text must be non-essential; the static PNG will show it complete |
| **Orbit** | `x = cx + r cos(2πp)`, `y = cy + r sin(2πp)` for a small satellite dot | Something monitored or in progress | Radius small (≤ 3% of canvas); no trails |

## Timing

- Loop length from the slowest motion: pulse and drift want 3–4 s; scan and draw 5–6 s; blink can nest inside any of them at an integer multiple of the loop frequency.
- Frame period 60–100 ms. Fewer frames per second look choppy on continuous motions (march, drift); more inflate the file with no visible gain at hero size.
- Easing only on motions that start and stop (draw, scan). Continuous motions (march, drift, orbit) must be linear in p or the seam shows as a speed change.

## What reads as "too much"

Whole-canvas motion; text that moves; layout that changes; bounce or elastic; two things pulsing; anything faster than about one event per second; motion on the element the eye needs for reading the data. If a reviewer says "nice animation" instead of commenting on the image, cut one layer.
