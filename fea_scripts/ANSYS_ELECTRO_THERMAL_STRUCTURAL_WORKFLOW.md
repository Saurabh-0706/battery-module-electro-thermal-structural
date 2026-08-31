# ANSYS Electro-Thermal-Structural Workflow

Three coupled physics, all inside the ANSYS Mechanical Student install you already have working -- no new software required for the core project (Maxwell/electromagnetics and PyMAPDL automation are optional stretch extensions, documented separately once the core is done).

Load values referenced below come from `electrical_python/discharge_heat_profile.py`: peak discharge current 15.0 A (3C pulse on a 5.0 Ah cell), peak per-cell Joule heat 4.5 W, 4 cells in series (4S1P).

## Geometry (build this in Fusion 360 first)

A simplified battery module: 4 cylindrical cells (Ø21mm x 70mm, "21700" format) arranged in a 2x2 grid inside a rectangular aluminum housing with a flat baseplate (the intended cooling surface), connected in series by a simple busbar strip across the top terminals. Exact dimensions to be finalized when we get to the CAD step -- this doc will be updated with the final STEP filename and hole/terminal positions once that's built.

## Step 1 -- Steady-State (or Transient) Electric Conduction

1. In ANSYS Workbench, drag a **Thermal-Electric** analysis system (this couples Electric Conduction and Thermal in one linked system -- look for it under Analysis Systems; if your version doesn't have a combined "Thermal-Electric" system, use a separate **Steady-State Electric Conduction** system and manually transfer its Joule Heat result into the Thermal system's Setup, the same way we linked Geometry/Model cells for the suspension-bracket comparison).
2. Import the module geometry.
3. Assign material to the busbar (e.g. Copper or Nickel -- check Engineering Data for resistivity; this determines how much the busbar itself heats up under 15A, separate from the cells).
4. Apply **Current** (15 A, from the Python script's peak) at one busbar terminal face, and a **Voltage = 0** (ground) reference at the other terminal face.
5. Solve. This computes the busbar's own Joule (I^2R) heating natively from its real geometry and resistivity -- this is the genuinely "electrical" physics in this project.

## Step 2 -- Thermal (the two heat sources combine here)

1. The busbar's Joule heating from Step 1 flows into the Thermal system automatically if you used the coupled Thermal-Electric system.
2. For the cells themselves: since ANSYS's simple electric-conduction solver doesn't model real battery electrochemistry, apply the **per-cell heat generation** computed by `discharge_heat_profile.py` directly as an **Internal Heat Generation** load on each cell body (Insert -> Heat -> Internal Heat Generation, or a volumetric heat flux, matching the Python script's Q_cell value -- convert W to W/m^3 using the cell's volume if the input needs a volumetric rate).
3. Apply a **Convection** boundary condition on the housing's exterior surfaces. Run this twice, as two design scenarios (this is the core "before/after" story of the project):
   - **Scenario A -- natural convection only**: h ~ 10 W/(m^2.K), representing no active cooling.
   - **Scenario B -- active cold-plate cooling**: a much higher effective h on the baseplate specifically (~500-1000 W/(m^2.K), typical for a liquid cold plate), representing the real mitigation an EV battery pack actually uses.
4. Run this as a **Transient Thermal** analysis (not just steady-state) using the ramp-hold-ramp current profile's timeline (0-900s from the Python script) so you get a genuine temperature-vs-time curve, the same way the suspension-bracket project used a genuinely transient structural solve rather than a static-equivalent one.
5. Record max temperature vs. time for both scenarios into `results/` -- this comparison (Scenario A likely showing a dangerous temperature rise consistent with the Python script's rough lumped estimate, Scenario B showing it controlled) is the central engineering finding of this project.

## Step 3 -- Structural (thermal stress)

1. Transfer the Thermal system's Solution into a new Static (or Transient) Structural system's Setup, the same linked-cell approach used for the clean static-vs-transient comparison in the suspension-bracket project -- this imports the temperature field automatically as a thermal body load.
2. Add mechanical boundary conditions: Fixed Support at the housing's actual mounting points (to be defined once the CAD is built).
3. Solve for max equivalent stress and deformation caused by thermal expansion -- this is where you'd catch a real failure mode like a busbar-to-terminal joint cracking from repeated thermal cycling (a natural fatigue extension later, reusing the rainflow/Miner's-rule code from the suspension-bracket project, applied to thermal stress cycles from repeated charge/discharge events instead of mechanical load cycles).

## What this feeds into next

- Scenario A vs. B temperature comparison -> the core "why active cooling matters" finding.
- Peak structural stress -> compare against material yield the same way Section 6 of the suspension-bracket report did.
- `postprocessing/lumped_thermal_check.py` -> analytical cross-check once Step 2's transient temperature data exists.
- Optional stretch: Maxwell (Ansys Electronics Desktop Student) for the magnetic field around the busbar under 15A, or PyMAPDL to script this whole workflow instead of the GUI.
