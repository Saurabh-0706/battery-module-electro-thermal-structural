"""
lumped_thermal_check.py

Formal analytical cross-check for this project -- plays the same role
analytical_beam_check.m played for the suspension-bracket project: an
independent, hand-calculation-based benchmark against the converged FEA
result, using a different method (lumped-capacitance thermal theory
instead of the FEA's full 3D conduction/convection solve).

Lumped-capacitance theory (valid when the cell's internal conduction
resistance is small compared to its surface convection resistance --
check the Biot number, Bi = h*Lc/k, is < ~0.1):

    m*cp * dT/dt = Q_gen(t) - h*A*(T - T_amb)

Scope note (an honest, deliberate limitation, not an oversight): this
single-node model is only checked against Scenario A (natural convection,
h=10 W/m^2K applied uniformly over the cell's own surface). Scenario B's
cold plate acts ONLY on the baseplate, not on the cell surface directly --
representing that properly needs a two-node model (cell node + housing
node, coupled by a conduction/contact resistance, with h*A only on the
housing node), which is out of scope for this simple check. Worse, the
Biot number at h=750 W/m^2K would be ~1.7 (>>0.1) if naively applied to
the bare cell surface -- lumped-capacitance theory would not even be
valid there, so attempting a naive Scenario-B single-node comparison
would be a genuinely wrong analysis, not just a rough one. This mirrors
the honest "know the limits of your method" documentation the
suspension-bracket project used for the beam-theory-near-the-support gap.

Usage:
    python lumped_thermal_check.py
Compares:
    - This script's predicted cell temperature-vs-time curve (Scenario A
      physics: bare-cell-surface convection at h=10 W/m^2K)
    - results/scenario_A_temperature_history.csv (Time, Min, Max, Avg),
      pasted from ANSYS's Transient Thermal solution the same manual
      paste-from-ANSYS-tabular-results workflow used throughout the
      suspension-bracket project. The FEA "Max" column (Cell 1, the
      hottest point) is the fair comparison target -- it is the same
      physical quantity this lumped model predicts (peak cell temperature).
"""

import csv
import math
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "electrical_python"))
from discharge_heat_profile import (
    current_profile,
    R_INTERNAL,
    TOTAL_DURATION_S,
    CELL_MASS_KG,
    CELL_CP,
    CELL_DIA_M,
    CELL_LEN_M,
    H_NATURAL_CONV,
)

T_AMB_C = 22.0


def main():
    # --- Cell surface area and Biot number check ---
    A_cell = math.pi * CELL_DIA_M * CELL_LEN_M + 2 * math.pi * (CELL_DIA_M / 2) ** 2
    V_cell = math.pi * (CELL_DIA_M / 2) ** 2 * CELL_LEN_M
    Lc = V_cell / A_cell
    k_cell = 2.0  # W/(m.K) -- matches the isotropic conductivity assigned in ANSYS
    Bi = H_NATURAL_CONV * Lc / k_cell
    print(f"Cell surface area: {A_cell*1e4:.2f} cm^2")
    print(f"Characteristic length Lc = V/A: {Lc*1e3:.3f} mm")
    print(f"Biot number (Scenario A, h={H_NATURAL_CONV} W/m^2K): {Bi:.4f}", end=" ")
    print("-> lumped-capacitance VALID (Bi << 0.1)" if Bi < 0.1 else "-> lumped-capacitance QUESTIONABLE")

    # For reference: why Scenario B isn't attempted this way
    Bi_hypothetical_B = 750.0 * Lc / k_cell
    print(f"(For reference: a naive h=750 W/m^2K applied directly to the cell "
          f"surface would give Bi={Bi_hypothetical_B:.2f} -- lumped theory would "
          f"NOT be valid there, which is why Scenario B is not cross-checked "
          f"with this single-node model; see module docstring.)")

    # --- Solve the lumped ODE for Scenario A physics ---
    def rhs(t, T):
        I = current_profile(np.array([t]))[0]
        Q_gen = I**2 * R_INTERNAL
        dTdt = (Q_gen - H_NATURAL_CONV * A_cell * (T[0] - T_AMB_C)) / (CELL_MASS_KG * CELL_CP)
        return [dTdt]

    t_eval = np.linspace(0, TOTAL_DURATION_S, 901)
    sol = solve_ivp(rhs, [0, TOTAL_DURATION_S], [T_AMB_C], t_eval=t_eval, max_step=1.0)
    T_lumped = sol.y[0]

    peak_lumped = np.max(T_lumped)
    t_peak_lumped = t_eval[np.argmax(T_lumped)]
    final_lumped = T_lumped[-1]
    print(f"\nLumped-model peak cell temperature: {peak_lumped:.2f} degC at t={t_peak_lumped:.0f}s")
    print(f"Lumped-model temperature at t=900s: {final_lumped:.2f} degC")

    # --- Read the FEA Scenario A result ---
    fea_path = Path(__file__).resolve().parent.parent / "results" / "scenario_A_temperature_history.csv"
    fea_t, fea_max = [], []
    with open(fea_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            fea_t.append(float(row["time_ms"]) / 1000.0)
            fea_max.append(float(row["max_C"]))
    fea_t = np.array(fea_t)
    fea_max = np.array(fea_max)

    peak_fea = np.max(fea_max)
    t_peak_fea = fea_t[np.argmax(fea_max)]
    final_fea = fea_max[-1]
    print(f"\nFEA (Scenario A, Cell 1 max) peak temperature: {peak_fea:.2f} degC at t={t_peak_fea:.0f}s")
    print(f"FEA temperature at t=900s: {final_fea:.2f} degC")

    pct_diff_peak = 100 * (peak_lumped - peak_fea) / peak_fea
    pct_diff_final = 100 * (final_lumped - final_fea) / final_fea
    print(f"\n--- Comparison ---")
    print(f"Peak temperature: lumped {peak_lumped:.2f} degC vs FEA {peak_fea:.2f} degC "
          f"({pct_diff_peak:+.1f}%)")
    print(f"t=900s temperature: lumped {final_lumped:.2f} degC vs FEA {final_fea:.2f} degC "
          f"({pct_diff_final:+.1f}%)")
    print("\nA double-digit-percent-scale gap here is expected and legitimate, not a bug:")
    print("the lumped model assumes the cell convects directly to ambient air, while")
    print("the real FEA cell is enclosed in a housing and has to conduct through the")
    print("housing before reaching ambient air at all -- a fundamentally different,")
    print("slower heat-rejection path than the lumped model assumes. The direction of")
    print("the gap (lumped model over- or under-predicting) is itself informative:")
    print("see the printed sign above.")

    # --- Plot ---
    results_dir = Path(__file__).resolve().parent.parent / "results"
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(t_eval, T_lumped, label="Lumped-capacitance model (analytical)", color="tab:orange")
    ax.plot(fea_t, fea_max, label="ANSYS Transient Thermal, Scenario A (Cell 1 max)",
             color="tab:blue", marker="o", markersize=3, linestyle="-")
    ax.axhline(T_AMB_C, color="gray", linestyle=":", linewidth=1, label="Ambient (22 degC)")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Temperature [degC]")
    ax.set_title("Analytical lumped-capacitance cross-check vs. FEA (Scenario A)")
    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    png_path = results_dir / "lumped_thermal_check.png"
    fig.savefig(png_path, dpi=150)
    print(f"\nWrote {png_path}")

    csv_path = results_dir / "lumped_vs_fea_comparison.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "lumped_model_C", "fea_scenarioA_max_C"])
        fea_interp = np.interp(t_eval, fea_t, fea_max)
        for ti, Tl, Tf in zip(t_eval, T_lumped, fea_interp):
            writer.writerow([f"{ti:.1f}", f"{Tl:.3f}", f"{Tf:.3f}"])
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()
