"""Generate the paper's results figures (PDF) from the recorded verdict data.

Figures:
  figs/fig_triangle.pdf — installation triangle: seat density / final CDS /
      trigger-light gate per arm, with bootstrap 95% CI whiskers where computed.
  figs/fig_register.pdf — synthesizer register: seat input density vs final
      output density per Lead, PRESERVE on/off, vs the perfect-transmission line.

Data are the committed verdict numbers (RUNBOOK_PAPER_HARDENING.md); this
script is regeneration, not analysis.

Run: .venv-train/bin/python docs/make_figs.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).parent / "figs"
OUT.mkdir(exist_ok=True)

INK = "#1a1a1a"
plt.rcParams.update({
    "font.family": "serif", "font.size": 9,
    "axes.edgecolor": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False,
})

ARM_COLORS = {
    "A′": "#8a8a85",       # baseline grey
    "Prompt": "#b5853a",        # amber
    "SFT": "#c7793f",           # deep amber
    "ORPO": "#2e6d5e",          # teal-green
    "CPO": "#6d8fc0",           # blue
}

# ---------------------------------------------------------------- fig 1: triangle
# arm: (seat mean, lo, hi), (final mean, lo, hi), gate
DATA = {
    "A′":   ((0.89, 0.69, 1.11), (0.859, 0.64, 1.08), 0.96),
    "Prompt": ((1.85, 1.42, 2.32), (0.590, 0.40, 0.81), 3.03),
    "SFT":    ((1.77, 1.46, 2.09), (0.575, 0.43, 0.73), 1.21),
    "ORPO":   ((0.87, 0.60, 1.17), (0.655, 0.49, 0.85), 0.15),
    "CPO":    ((0.56, 0.34, 0.80), (0.638, 0.49, 0.80), 0.37),
}

fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.4))
panels = [
    ("Seat density (trigger cases)", 0, "behaviors / 1k chars"),
    ("Final-output CDS", 1, "CDS"),
    ("Trigger-light gate (case 7)", 2, "behaviors / 1k chars"),
]
arms = list(DATA)
for ax, (title, idx, ylab) in zip(axes, panels):
    xs = range(len(arms))
    for x, arm in zip(xs, arms):
        d = DATA[arm][idx]
        if idx < 2:
            mean, lo, hi = d
            ax.bar(x, mean, 0.62, color=ARM_COLORS[arm], zorder=3)
            ax.errorbar(x, mean, yerr=[[mean - lo], [hi - mean]],
                        fmt="none", ecolor=INK, elinewidth=1.0, capsize=2.5, zorder=4)
        else:
            ax.bar(x, d, 0.62, color=ARM_COLORS[arm], zorder=3)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(arms, fontsize=8, rotation=25, ha="right")
    ax.set_title(title, fontsize=9)
    ax.set_ylabel(ylab, fontsize=8)
    ax.tick_params(labelsize=8)
    ax.margins(y=0.08)
# annotate the gate panel: correct value is zero
axes[2].axhline(DATA["A′"][2], color="#8a8a85", lw=0.8, ls=":", zorder=2)
axes[2].annotate("baseline", xy=(4.35, DATA["A′"][2]), fontsize=7,
                 color="#8a8a85", va="center")
fig.tight_layout(w_pad=1.6)
fig.savefig(OUT / "fig_triangle.pdf", bbox_inches="tight")
plt.close(fig)
print("wrote figs/fig_triangle.pdf")

# ---------------------------------------------------------------- fig 2: register
# Lead: [(seat_in, out) PRESERVE base, hot], [(seat_in, out) noPRESERVE base, hot]
REG = {
    "Phi-4-14B":  {"on": [(0.78, 1.17), (1.42, 0.61)], "off": [(0.54, 0.52), (2.15, 0.31)]},
    "gpt-oss-20B": {"on": [(0.87, 0.63), (1.81, 0.86)], "off": [(0.86, 0.20), (2.33, 0.13)]},
    "Qwen2.5-7B": {"on": [(0.79, 1.24), (2.41, 1.06)], "off": [(0.92, 0.24), (1.93, 0.62)]},
}
LEAD_COLORS = {"Phi-4-14B": "#c7793f", "gpt-oss-20B": "#2e6d5e", "Qwen2.5-7B": "#6d8fc0"}

fig, ax = plt.subplots(figsize=(4.6, 3.1))
ax.plot([0, 2.6], [0, 2.6], color="#bbbbb5", lw=0.9, ls="--", zorder=1)
ax.annotate("perfect transmission\n(output = input)", xy=(2.02, 2.14), fontsize=7,
            color="#8a8a85", rotation=38, ha="center", va="bottom")
for lead, series in REG.items():
    c = LEAD_COLORS[lead]
    for key, ls, lw, alpha in (("on", "-", 1.8, 1.0), ("off", ":", 1.4, 0.85)):
        pts = series[key]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        ax.plot(xs, ys, ls, color=c, lw=lw, alpha=alpha, zorder=3,
                marker="o", markersize=3.5)
ax.set_xlabel("seat input density (behaviors / 1k chars)", fontsize=8)
ax.set_ylabel("final output density", fontsize=8)
ax.tick_params(labelsize=8)
ax.set_xlim(0.3, 2.6); ax.set_ylim(0, 2.6)
# legends: leads by color; PRESERVE by linestyle
from matplotlib.lines import Line2D
lead_handles = [Line2D([0], [0], color=LEAD_COLORS[l], lw=1.8, label=l) for l in REG]
style_handles = [Line2D([0], [0], color=INK, lw=1.6, ls="-", label="PRESERVE on"),
                 Line2D([0], [0], color=INK, lw=1.3, ls=":", label="PRESERVE off")]
leg1 = ax.legend(handles=lead_handles, loc="upper left", fontsize=7, frameon=False)
ax.add_artist(leg1)
ax.legend(handles=style_handles, loc="lower right", fontsize=7, frameon=False)
ax.annotate("Phi-4 inverts:\nhotter input, lower output", xy=(1.42, 0.61),
            xytext=(1.62, 1.55), fontsize=7,
            arrowprops=dict(arrowstyle="->", lw=0.7, color=INK))
fig.tight_layout()
fig.savefig(OUT / "fig_register.pdf", bbox_inches="tight")
plt.close(fig)
print("wrote figs/fig_register.pdf")

# ---------------------------------------------------------------- fig 0: schematic
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

fig, ax = plt.subplots(figsize=(6.8, 2.5))
ax.set_xlim(0, 10); ax.set_ylim(0, 3.75); ax.axis("off")

def box(x, y, w, h, label, sub=None, lw=1.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                fc="white", ec=INK, lw=lw))
    ax.text(x + w/2, y + h/2 + (0.13 if sub else 0), label, ha="center",
            va="center", fontsize=8.5)
    if sub:
        ax.text(x + w/2, y + h/2 - 0.22, sub, ha="center", va="center",
                fontsize=6.5, color="#6b6b66")

# seats + their emitted-density bars (heights vary by arm/training)
seats = [("legal seat", "Saul-7B", 2.30, 1.05),
         ("healthcare seat", "Med42-8B", 1.25, 0.72),
         ("finance seat", "Qwen-Fin-8B", 0.20, 0.85)]
for name, sub, y, dens in seats:
    box(0.25, y, 1.95, 0.78, name, sub)
    ax.add_patch(Rectangle((2.36, y + 0.10), 0.13, dens * 0.62,
                           fc="#c7793f", ec="none"))
ax.text(1.22, 3.68, "seat disposition varies with arm\n(prompting / SFT / ORPO / CPO)",
        fontsize=6.5, color="#6b6b66", ha="center", va="top")

# synthesizer with register band
sx, sy, sw, sh = 4.35, 0.55, 2.6, 2.25
ax.add_patch(FancyBboxPatch((sx, sy), sw, sh, boxstyle="round,pad=0.06",
                            fc="white", ec=INK, lw=1.4))
ax.text(sx + sw/2, sy + sh - 0.24, "synthesizer (Lead)", ha="center",
        fontsize=8.5, fontweight="bold")
band_y, band_h = sy + 0.78, 0.55
ax.add_patch(Rectangle((sx + 0.18, band_y), sw - 0.36, band_h,
                       fc="#e5e2dc", ec="none"))
ax.text(sx + sw/2, band_y + band_h/2, "register band\n(writer-specific)",
        ha="center", va="center", fontsize=6.8)
ax.annotate("PRESERVE instructions = gain control", xy=(sx + sw/2, band_y - 0.06),
            xytext=(sx + sw/2, sy + 0.16), fontsize=6.5, ha="center",
            color="#6b6b66", arrowprops=dict(arrowstyle="-", lw=0.6, color="#6b6b66"))

# arrows seats -> synthesizer
for _, _, y, _ in seats:
    ax.add_patch(FancyArrowPatch((2.62, y + 0.39), (sx - 0.06, sy + sh/2),
                                 arrowstyle="-|>", mutation_scale=9,
                                 lw=0.9, color=INK, shrinkA=0, shrinkB=0))

# output: bar clamped to band height
box(8.0, 1.25, 1.7, 0.78, "final answer")
ax.add_patch(Rectangle((9.82, 1.35), 0.13, band_h * 0.62, fc="#2e6d5e", ec="none"))
ax.add_patch(FancyArrowPatch((sx + sw + 0.06, sy + sh/2), (7.94, 1.64),
                             arrowstyle="-|>", mutation_scale=9, lw=0.9, color=INK))
ax.text(8.85, 0.78, r"output $\approx f(\mathrm{register}\times\mathrm{instructions})$"
        + "\nnearly independent of seat input",
        fontsize=6.5, color="#6b6b66", ha="center", va="top")

fig.savefig(OUT / "fig_schematic.pdf", bbox_inches="tight")
plt.close(fig)
print("wrote figs/fig_schematic.pdf")

# ------------------------------------------------- fig 3: gain curve + additivity
GAIN = {  # lead -> mean final density at k=0..3 (6 cases per cell)
    "Phi-4-14B":  [0.52, 0.58, 1.53, 0.68],
    "gpt-oss-20B": [0.16, 0.27, 0.41, 0.53],
    "Qwen2.5-7B": [0.57, 1.00, 0.95, 1.21],
}
ADD = {  # hot-seat count -> (mean, lo, hi)
    0: (1.01, 0.55, 1.55), 1: (1.03, 0.43, 1.63),
    2: (0.84, 0.63, 1.05), 3: (0.64, 0.29, 1.01),
}

fig, (axg, axa) = plt.subplots(1, 2, figsize=(7.0, 2.6),
                               gridspec_kw={"width_ratios": [1.15, 1]})
ks = [0, 1, 2, 3]
for lead, vals in GAIN.items():
    axg.plot(ks, vals, "-o", color=LEAD_COLORS[lead], lw=1.8, markersize=4,
             label=lead)
# flag the Phi-4 k=2 anomaly
axg.plot([2], [GAIN["Phi-4-14B"][2]], "o", mfc="white",
         mec=LEAD_COLORS["Phi-4-14B"], markersize=6, zorder=5)
axg.annotate("anomalous cell\n(n=6, sd 0.62)", xy=(2, 1.53), xytext=(0.75, 1.42),
             fontsize=6.5, color="#6b6b66",
             arrowprops=dict(arrowstyle="->", lw=0.6, color="#6b6b66"))
axg.set_xticks(ks)
axg.set_xlabel("PRESERVE clauses retained (k)", fontsize=8)
axg.set_ylabel("final-output density", fontsize=8)
axg.set_title("Instructions: graded gain control", fontsize=9)
axg.legend(fontsize=6.5, frameon=False, loc="upper left")
axg.tick_params(labelsize=8)

hs = sorted(ADD)
means = [ADD[h][0] for h in hs]
axa.errorbar(hs, means,
             yerr=[[ADD[h][0] - ADD[h][1] for h in hs],
                   [ADD[h][2] - ADD[h][0] for h in hs]],
             fmt="-o", color="#c7793f", lw=1.8, markersize=4,
             ecolor=INK, elinewidth=0.9, capsize=2.5)
axa.set_xticks(hs)
axa.set_ylim(0, 1.8)
axa.set_xlabel("hot seats (h of 3)", fontsize=8)
axa.set_ylabel("final-output density", fontsize=8)
axa.set_title("Seat input: non-additive", fontsize=9)
axa.annotate(r"$\rho = -0.80$: heating all seats" + "\nadds nothing at the mouth",
             xy=(1.45, 1.55), fontsize=6.5, color="#6b6b66", ha="center")
axa.tick_params(labelsize=8)
fig.tight_layout(w_pad=2.0)
fig.savefig(OUT / "fig_gain.pdf", bbox_inches="tight")
plt.close(fig)
print("wrote figs/fig_gain.pdf")
