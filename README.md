# Electro-Thermal-Structural Simulation of an EV Battery Module

A self-contained, computational engineering project combining electrical-conduction FEA (Joule heating), transient thermal analysis, and thermal-stress structural analysis, with the electrical load derived from real battery physics in Python rather than assumed. No lab access, no proprietary company standard, and no physical test rig required — verification comes from an analytical lumped-capacitance cross-check and a documented before/after cooling-scenario comparison.

## Problem Statement

EV and portable-electronics battery modules generate significant heat under high-current events (fast charging, hard acceleration, fast discharge) due to internal resistive (I²R) losses in the cells and the busbars connecting them. Left uncooled, this heat can drive cells to dangerous temperatures — a real, safety-critical design problem, not an academic one. This project builds a small, physically-grounded pipeline that: (1) derives a realistic high-current discharge event from actual cell parameters rather than a guessed heat input, (2) computes the resulting Joule heating in both the cells and the busbar via a real electrical-conduction FEA solve, (3) solves the transient temperature field under two cooling scenarios — natural convection only vs. an active cold-plate — to quantify why active cooling matters, and (4) feeds that temperature field into a structural analysis to check thermal stress on the housing and busbar joints.

## Why Python + a Real Electrical-Conduction Solve (Not a Guessed Heat Input)

The weak version of a "battery thermal simulation" project just applies an assumed, round-number heat load (e.g. "assume 20W and move on") directly to a thermal model. The stronger version — and the reason this project derives its own electrical load rather than assuming one — is:

- A **discharge current profile** is derived in Python (`electrical_python/discharge_heat_profile.py`) from real cell parameters (5.0 Ah capacity, 20 mΩ internal resistance) at a realistic 3C worst-case thermal-design pulse — the same rigor as deriving a dynamic load from a quarter-car model rather than assuming a static g-factor, applied here to an electrical rather than mechanical load case.
- That current is fed into a real **Electric Conduction** FEA solve in ANSYS Mechanical, which computes the busbar's own Joule heating from its actual geometry and material resistivity — genuine electrical physics, not a lookup number.
- The cells' own heat generation (computed in Python, since ANSYS's basic conduction solver doesn't model real electrochemistry) and the busbar's FEA-computed Joule heating both feed into a **Transient Thermal** solve, run under two cooling scenarios to make the "why does this matter" case quantitatively rather than by assertion.
- The resulting temperature field feeds a **Structural** analysis for thermal stress — completing an Electrical → Thermal → Structural chain, genuine 3-domain multiphysics.

## Tools Used

| Purpose | Tool |
|---|---|
| Electrical load derivation | Python (NumPy, Matplotlib) |
| Parametric CAD | Autodesk Fusion 360 |
| Electric conduction (Joule heating) | ANSYS Mechanical Student — Electric Conduction / Thermal-Electric |
| Transient thermal | ANSYS Mechanical Student — Transient Thermal |
| Structural (thermal stress) | ANSYS Mechanical Student — Static/Transient Structural |
| Analytical cross-check | Python (lumped-capacitance thermal model) |
| Optional stretch: electromagnetics | Ansys Electronics Desktop Student (Maxwell) — separate free download, not required for the core project |
| Optional stretch: scripted automation | PyMAPDL |
| Documentation | Markdown, Git |

## Methodology

1. **Electrical load derivation (Python)** — a realistic 3C discharge/fast-charge current pulse (ramp-hold-ramp, not an unphysical step) derived from real 21700-cell parameters; per-cell Joule heating computed from the cell's own internal resistance.
2. **Baseline CAD model** — a 4-cell (2×2, 4S1P series) battery module in Fusion 360: cylindrical cells, aluminum housing with a baseplate, busbar.
3. **Electric conduction (ANSYS Mechanical, native)** — apply the derived current to the busbar terminals; solve for the busbar's own Joule heating from real geometry and resistivity.
4. **Transient thermal (ANSYS Mechanical, native)** — combine the busbar's FEA-computed Joule heating with the cells' Python-computed internal heat generation; solve twice, under natural-convection-only and active-cold-plate cooling scenarios, to quantify the effect of active cooling.
5. **Analytical cross-check (Python)** — an independent lumped-capacitance thermal model benchmarked against the converged transient FEA temperature curve, the same "never trust one model alone" principle used throughout the companion suspension-bracket project.
6. **Structural (ANSYS Mechanical, native)** — import the thermal field as a body load; solve for thermal stress and deformation at the housing/busbar mounting points.
7. **Reporting** — methodology, assumptions, the natural-convection-vs-cold-plate comparison, the analytical cross-check, and thermal-stress results, with plots.

## Repository Structure

```
battery-module-electro-thermal-structural/
├── README.md
├── cad/                    # Fusion 360 file + STEP export of the battery module
├── electrical_python/      # discharge_heat_profile.py -- derives the electrical load
├── fea_scripts/            # ANSYS electro-thermal-structural workflow notes
├── postprocessing/         # lumped-capacitance analytical cross-check
├── report/                 # final write-up and figures
└── results/                # raw result data (CSV), plots, temperature/stress histories
```

## What This Demonstrates

- **Multiphysics simulation** — a genuine 3-domain Electrical → Thermal → Structural coupled analysis, not a single-physics FEA project
- **Physics-derived loading, not assumed inputs** — the electrical load comes from real cell parameters and a realistic worst-case discharge event, the same discipline as the companion suspension-bracket project's dynamics-derived mechanical load
- **Python for engineering automation/analysis** — pre-processing (load derivation) and post-processing (analytical cross-check), demonstrating a second scripting language alongside the companion project's MATLAB work
- **A real, quantified design decision** — natural convection vs. active cooling isn't asserted, it's computed and compared, directly relevant to EV/battery-industry thermal management roles
- **Structural verification methodology carried over** — analytical cross-check, honest documentation of where a simplified model does and doesn't hold, consistent with the companion project's approach
- **Optional stretch scope for electromagnetics and scripted automation** — clearly separated from the core deliverable so the project ships a solid result first

## Feasibility Note

Every core step is achievable with free/student licenses already installed (ANSYS Mechanical Student, Fusion 360, Python) and requires no physical test rig, lab booking, cell testing equipment, or confidential company data. Verification comes from an analytical lumped-capacitance cross-check and a documented, physically-motivated cooling-scenario comparison — not physical-test correlation.

## Status

Project scoped; electrical load derivation script (`electrical_python/discharge_heat_profile.py`) written and verified — peak discharge current 15.0 A (3C), peak per-cell Joule heat 4.5 W, and a rough natural-convection sanity check already shows a ~85°C temperature rise, motivating the active-cooling comparison this project is built around. Next: CAD geometry in Fusion 360.
