"""
plot_scenario_comparison.py

Plots Scenario A (natural convection) vs Scenario B (active cold plate)
side by side -- the central "why active cooling matters" comparison this
project is built around. Reads the two saved ANSYS result CSVs directly
(no re-solve needed).
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_history(path):
    t, mn, mx, avg = [], [], [], []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            t.append(float(row["time_ms"]) / 1000.0)
            mn.append(float(row["min_C"]))
            mx.append(float(row["max_C"]))
            avg.append(float(row["avg_C"]))
    return t, mn, mx, avg


def main():
    results_dir = Path(__file__).resolve().parent.parent / "results"
    tA, minA, maxA, avgA = read_history(results_dir / "scenario_A_temperature_history.csv")
    tB, minB, maxB, avgB = read_history(results_dir / "scenario_B_temperature_history.csv")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.plot(tA, maxA, color="tab:red", label="Max (Cell 1)", linewidth=2)
    ax1.plot(tA, minA, color="tab:blue", label="Min (Wall Ring)", linewidth=2)
    ax1.axhline(22, color="gray", linestyle=":", linewidth=1, label="Ambient (22 degC)")
    ax1.set_title("Scenario A -- Natural Convection Only (h=10 W/m2K)")
    ax1.set_xlabel("Time [s]")
    ax1.set_ylabel("Temperature [degC]")
    ax1.set_ylim(20, 65)
    ax1.legend(fontsize=9)
    ax1.grid(True)

    ax2.plot(tB, maxB, color="tab:red", label="Max (Cell 1)", linewidth=2)
    ax2.plot(tB, minB, color="tab:blue", label="Min (Baseplate/Wall Ring)", linewidth=2)
    ax2.axhline(22, color="gray", linestyle=":", linewidth=1, label="Ambient (22 degC)")
    ax2.set_title("Scenario B -- Active Cold Plate (h=750 W/m2K on baseplate)")
    ax2.set_xlabel("Time [s]")
    ax2.set_ylabel("Temperature [degC]")
    ax2.set_ylim(20, 65)
    ax2.legend(fontsize=9)
    ax2.grid(True)

    fig.suptitle("Battery Module Transient Thermal Response: Natural Convection vs. Active Cold Plate",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    out_path = results_dir / "scenario_comparison_A_vs_B.png"
    fig.savefig(out_path, dpi=150)
    print(f"Wrote {out_path}")

    # Overlay plot -- both Max curves on one axis, the single clearest "so what" figure
    fig2, ax = plt.subplots(figsize=(8, 5))
    ax.plot(tA, maxA, color="tab:red", linestyle="-", linewidth=2, label="Scenario A (natural convection) -- Cell Max")
    ax.plot(tB, maxB, color="tab:orange", linestyle="-", linewidth=2, label="Scenario B (cold plate) -- Cell Max")
    ax.plot(tA, minA, color="tab:blue", linestyle="--", linewidth=1.5, label="Scenario A -- Housing Min")
    ax.plot(tB, minB, color="tab:green", linestyle="--", linewidth=1.5, label="Scenario B -- Housing Min")
    ax.axhline(22, color="gray", linestyle=":", linewidth=1, label="Ambient (22 degC)")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Temperature [degC]")
    ax.set_title("Cell peak & housing temperature: Scenario A vs. Scenario B")
    ax.legend(fontsize=9)
    ax.grid(True)
    fig2.tight_layout()
    out_path2 = results_dir / "scenario_comparison_overlay.png"
    fig2.savefig(out_path2, dpi=150)
    print(f"Wrote {out_path2}")


if __name__ == "__main__":
    main()
