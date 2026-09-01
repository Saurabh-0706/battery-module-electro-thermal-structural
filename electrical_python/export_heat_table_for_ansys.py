"""
export_heat_table_for_ansys.py

Produces the per-cell volumetric heat-generation table for ANSYS's
Transient Thermal "Internal Heat Generation" load -- the thermal-domain
equivalent of export_load_table_for_ansys.m in the suspension-bracket
project (which downsampled a noisy dynamic force history for ANSYS's
Tabular Data grid).

This one is actually simpler than the bracket case, and it's worth
explaining why: the bracket's dynamic load came from an ODE solve of a
bumpy road input -- genuinely non-smooth, so we had to downsample while
preserving the true peak sample. The battery module's current_profile(t)
is, by construction, an EXACT piecewise-linear trapezoid (ramp / hold /
ramp / off). ANSYS's Tabular Data does linear interpolation between the
points you give it -- so a piecewise-linear input is represented EXACTLY
by just its corner points. No downsampling algorithm needed here; this
script computes the corner times analytically rather than sampling an
array, which is actually more precise than pulling points from
discharge_heat_profile.py's 2000-point array.

Usage:
    python export_heat_table_for_ansys.py
Produces:
    - results/ansys_heat_generation_table.csv
    - a printed tab-separated Time(ms) / Heat Generation (W/mm^3) block,
      ready to paste directly into ANSYS Mechanical's Tabular Data grid
      for the Internal Heat Generation load on each cell body.

IMPORTANT -- unit system: this ANSYS project uses the mm-based unit
system (Metric: mm, g, N, ms, V, A -- confirmed from the Electric
Conduction step). Volumetric heat generation in that unit system is
W/mm^3, and time fields are in ms, NOT seconds. Both conversions are
done explicitly below. As with the busbar resistivity units earlier in
this project, double-check the unit dropdown next to the Internal Heat
Generation magnitude field in Mechanical's Details pane before pasting
values in -- a silent W/m^3-vs-W/mm^3 mismatch is a 1e9x error, and a
silent s-vs-ms mismatch is a 1000x error on the timeline.
"""

import csv
import math
from pathlib import Path

from discharge_heat_profile import (
    CAPACITY_AH,
    C_RATE,
    R_INTERNAL,
    RAMP_S,
    PULSE_DURATION_S,
    TOTAL_DURATION_S,
    CELL_DIA_M,
    CELL_LEN_M,
)


def main():
    I_peak = C_RATE * CAPACITY_AH                      # [A]
    Q_cell_peak = I_peak**2 * R_INTERNAL                # [W]

    cell_volume_m3 = math.pi * (CELL_DIA_M / 2) ** 2 * CELL_LEN_M
    cell_volume_mm3 = cell_volume_m3 * 1e9

    q_gen_peak_W_per_m3 = Q_cell_peak / cell_volume_m3
    q_gen_peak_W_per_mm3 = Q_cell_peak / cell_volume_mm3

    # Exact corner times of the trapezoidal profile [s]
    t_ramp_end = RAMP_S
    t_hold_end = RAMP_S + PULSE_DURATION_S
    t_ramp_down_end = t_hold_end + RAMP_S
    t_final = TOTAL_DURATION_S

    corners_s = [0.0, t_ramp_end, t_hold_end, t_ramp_down_end, t_final]
    corners_q_W = [0.0, Q_cell_peak, Q_cell_peak, 0.0, 0.0]

    print(f"Cell volume: {cell_volume_m3*1e6:.3f} cm^3 ({cell_volume_mm3:.1f} mm^3)")
    print(f"Peak per-cell Joule heat: {Q_cell_peak:.3f} W")
    print(f"Peak volumetric heat generation: {q_gen_peak_W_per_m3:.1f} W/m^3 "
          f"= {q_gen_peak_W_per_mm3:.6e} W/mm^3")

    results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(exist_ok=True)
    csv_path = results_dir / "ansys_heat_generation_table.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "time_ms", "Q_cell_W",
                          "q_gen_W_per_m3", "q_gen_W_per_mm3"])
        for ts, Qw in zip(corners_s, corners_q_W):
            q_m3 = Qw / cell_volume_m3
            q_mm3 = Qw / cell_volume_mm3
            writer.writerow([f"{ts:.4f}", f"{ts*1000:.4f}", f"{Qw:.4f}",
                              f"{q_m3:.4f}", f"{q_mm3:.10e}"])
    print(f"\nWrote {csv_path}")

    print("\nPaste this into ANSYS Mechanical's Tabular Data grid for the")
    print("Internal Heat Generation load on EACH cell body")
    print("(Time in ms, Heat Generation in W/mm^3 -- confirm units in the")
    print("Details pane match before pasting):\n")
    print("Time [ms]\tHeat Generation [W/mm^3]")
    for ts, Qw in zip(corners_s, corners_q_W):
        q_mm3 = Qw / cell_volume_mm3
        print(f"{ts*1000:.1f}\t{q_mm3:.6e}")


if __name__ == "__main__":
    main()
