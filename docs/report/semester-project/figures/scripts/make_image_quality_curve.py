#!/usr/bin/env python3
"""Analytic image-quality Lorentzian for the semester report (Fig. image-quality-curve)."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parents[1] / "fig_image_quality_curve.png"


def main() -> None:
    r = 0.30
    delta = np.linspace(0, 1.2, 400)
    q = r / (delta + r)
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    ax.plot(delta, q, color="#007A96", lw=2, label=r"$q=r/(\delta+r)$, $r=0.30$ m")
    for d, qv, lab in [
        (0.76, 0.28, "nadir, at rest"),
        (0.38, 0.44, "half-tracking"),
        (0.0, 1.0, "full tracking"),
    ]:
        ax.plot(d, qv, "o", color="#C45C26", ms=7, zorder=3)
        ax.annotate(lab, (d, qv), textcoords="offset points", xytext=(8, 8), fontsize=8)
    ax.set_xlabel(r"ground blur $\delta$ [m]")
    ax.set_ylabel(r"image quality $q$")
    ax.set_xlim(0, 1.2)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(OUT, dpi=200)
    print(OUT)


if __name__ == "__main__":
    main()
