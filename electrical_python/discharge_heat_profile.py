"""
discharge_heat_profile.py

Derives a physically-grounded electrical load for the battery module FEA,
instead of an assumed/guessed heat input -- the same principle behind the
quarter-car dynamics model in the suspension-bracket project: never feed
FEA a made-up number when you can derive it from the actual physics of
the load case.

Module: 4 cylindrical 21700-format Li-ion cells (21mm dia x 70mm), wired
in series (4S1P), connected by a busbar. A 4S series pack carries the SAME
current through every cell and through the busbar -- that's what makes
this a clean, well-posed electrical-conduction problem for ANSYS: one
current magnitude, applied at the busbar terminals.

Load case: a sustained 3C discharge/fast-charge pulse. This isn't an
arbitrary choice -- 3C is a realistic "worst-case thermal design" pulse
used in real EV/battery thermal validation (short high-current bursts,
e.g. fast charging or a hard acceleration event), and it's exactly the
kind of load a thermal-structural FEA needs to be checked against, not a
gentle average driving load.

Usage:
    python discharge_heat_profile.py
Produces:
    - results/discharge_current_profile.csv   (Time, Current, Q_per_cell)
    - results/discharge_profile.png            (plot, for the report)
    - a printed summary + a rough lumped-capacitance sanity check
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv
import math
from pathlib import Path

# --- Cell and pack parameters (typical high-performance 21700 Li-ion cell) ---
CAPACITY_AH = 5.0          # [Ah] nominal cell capacity
R_INTERNAL = 0.020         # [ohm] internal resistance (DC, includes tabs/foil)
N_SERIES = 4                # 4S1P module -- same current through every cell + busbar
C_RATE = 3.0                 # sustained fast-discharge/fast-charge pulse
RAMP_S = 2.0                  # [s] current ramp-up/down time (avoids an unphysical
                               #     instantaneous step, same reasoning as windowing
                               #     the road-bump input in the suspension project)
PULSE_DURATION_S = 600.0      # [s] 10-minute sustained high-current event
TOTAL_DURATION_S = 900.0      # [s] simulate 5 extra minutes of cool-down after the pulse
N_POINTS = 2000

# --- Cell physical properties, for the rough lumped-capacitance sanity check ---
CELL_MASS_KG = 0.070          # [kg] typical 21700 cell mass
CELL_CP = 900.0                # [J/(kg.K)] average specific heat of a cylindrical Li-ion cell
CELL_DIA_M = 0.021
CELL_LEN_M = 0.070
H_NATURAL_CONV = 10.0           # [W/(m^2.K)] natural (still-air) convection -- the
                                  # "worst case, no active cooling" scenario this
                                  # project is specifically built to stress-test


def current_profile(t):
    """Trapezoidal current pulse: ramp up, hold at I_peak, ramp down.
    Same 'smooth the load, don't feed FEA a discontinuity' logic as the
    windowed road-bump input in the suspension-bracket project."""
    I_peak = C_RATE * CAPACITY_AH
    I = np.zeros_like(t)
    t_end = RAMP_S + PULSE_DURATION_S
    ramp_up = (t >= 0) & (t < RAMP_S)
    hold = (t >= RAMP_S) & (t < t_end)
    ramp_down = (t >= t_end) & (t < t_end + RAMP_S)
    I[ramp_up] = I_peak * (t[ramp_up] / RAMP_S)
    I[hold] = I_peak
    I[ramp_down] = I_peak * (1 - (t[ramp_down] - t_end) / RAMP_S)
    return I


def main():
    t = np.linspace(0, TOTAL_DURATION_S, N_POINTS)
    I = current_profile(t)
    Q_cell = I**2 * R_INTERNAL          # [W] Joule heating per cell (same for all N_SERIES cells)

    peak_I = np.max(I)
    peak_Q_cell = np.max(Q_cell)
    total_pack_Q = peak_Q_cell * N_SERIES

    print(f"Peak discharge current: {peak_I:.2f} A ({C_RATE:.1f}C on a {CAPACITY_AH:.1f}Ah cell)")
    print(f"Peak per-cell Joule heat: {peak_Q_cell:.3f} W")
    print(f"Peak total pack heat ({N_SERIES}S): {total_pack_Q:.3f} W")

    # --- Rough lumped-capacitance sanity check (natural convection only) ---
    # This is NOT the formal analytical cross-check (that comes later, once
    # real FEA transient temperature data exists -- see postprocessing/
    # lumped_thermal_check.py). This is just an order-of-magnitude gut check
    # on the numbers above, and it already tells an important story:
    A_cell = math.pi * CELL_DIA_M * CELL_LEN_M + 2 * math.pi * (CELL_DIA_M / 2) ** 2
    tau = CELL_MASS_KG * CELL_CP / (H_NATURAL_CONV * A_cell)
    dT_steady_state = peak_Q_cell / (H_NATURAL_CONV * A_cell)

    print(f"\nRough lumped-capacitance check (natural convection only, h={H_NATURAL_CONV} W/m^2K):")
    print(f"  Cell surface area: {A_cell*1e4:.2f} cm^2")
    print(f"  Thermal time constant: {tau:.0f} s (~{tau/60:.1f} min)")
    print(f"  Estimated steady-state temperature rise above ambient: {dT_steady_state:.1f} degC")
    print("  -> With natural convection alone, sustained 3C discharge drives the cells")
    print("     to a dangerously high temperature rise. This is the real-world reason")
    print("     EV battery modules need active cooling (e.g. a liquid cold plate),")
    print("     not just a housing with vents -- and it's exactly what the ANSYS")
    print("     thermal model should be used to demonstrate quantitatively.")

    # --- Write results ---
    results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(exist_ok=True)
    csv_path = results_dir / "discharge_current_profile.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "current_A", "heat_per_cell_W"])
        for ti, Ii, Qi in zip(t, I, Q_cell):
            writer.writerow([f"{ti:.4f}", f"{Ii:.4f}", f"{Qi:.4f}"])
    print(f"\nWrote {csv_path}")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax1.plot(t, I, color="tab:blue")
    ax1.set_ylabel("Current [A]")
    ax1.set_title("Battery module discharge current profile (3C pulse)")
    ax1.grid(True)
    ax2.plot(t, Q_cell, color="tab:red")
    ax2.set_ylabel("Per-cell Joule heat [W]")
    ax2.set_xlabel("Time [s]")
    ax2.set_title("Per-cell resistive (I^2R) heat generation")
    ax2.grid(True)
    fig.tight_layout()
    png_path = results_dir / "discharge_profile.png"
    fig.savefig(png_path, dpi=150)
    print(f"Wrote {png_path}")


if __name__ == "__main__":
    main()
