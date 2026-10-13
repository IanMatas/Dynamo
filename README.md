# Wave Hall — Dynamo for Revit 2026

A reference-inspired architectural concept model with a broad, elevated crossing roof ribbon sweeping over a flowing oval hall, central skylight and grid, panelled facades, glazed entrance with fins, support piers, and ground slab.

**Overall dimensions: 130 m long × 75 m wide × 40 m maximum height.** These are the overall geometry bounds, measured from ground at Z = 0. X is length; Y is width. The model is centred on the Revit internal origin. The photos are interpreted conceptually; their exact geometry cannot be recovered from perspective images alone.

## Run in Revit

1. Download `Wave_Hall_Revit2026.dyn`.
2. In **Revit 2026**, open a project (`.rvt`), preferably a new architectural project, and open its default 3D view.
3. Choose **Manage → Dynamo**, then open the `.dyn` file. Use Dynamo inside Revit, not Dynamo Sandbox.
4. Keep run mode **Manual**. The graph's Python node uses **CPython3**. No third-party node packages or external Python files are required.
5. Click **Run**. Allow the tessellated components to build. The node output reports the model key, dimensions, element list, and triangle count.
6. Return to Revit, use **Zoom to Fit**, and select **Shaded** or **Consistent Colors**. Ensure **Generic Models** are visible and any section box includes the internal origin and Z = 0–40 m. Save your project as an `.rvt` file.

If Dynamo reports a Python engine error, confirm CPython3 is available in the Dynamo installation shipped with Revit 2026. If it reports an API error, the Python node warning contains the exact exception needed to diagnose it. Actual Revit execution has not been verified on this Linux workspace. If you already have an older version open in Dynamo, close that graph and open this updated file again; Dynamo continues to run the graph currently loaded in its workspace.

## Controls

Edit the seven code blocks, in order from top to bottom, retaining their semicolons:

| Control | Default | Meaning |
|---|---:|---|
| Length | `130.0;` | Overall X dimension in metres |
| Width | `75.0;` | Overall Y dimension in metres |
| Height | `40.0;` | Maximum height above ground in metres |
| Opening length | `48.0;` | Nominal oval opening X dimension |
| Opening width | `40.0;` | Nominal oval opening Y dimension |
| Segments | `128;` | Smoothness: a multiple of 4 from 64 to 256 |
| Model key | `"WaveHall_01";` | Identity used to find and update this generated model |

Metres are converted to Revit internal feet, independently of project display units. The final geometry is normalized to the requested overall bounds, including fins and roof joints; nominal opening dimensions can change very slightly in that normalization.

Use the same model key to update the same ten generated components. Use another key to create another model at the same origin. A rerun resets manually moved geometry for that key to the graph's coordinates. Only DirectShapes tagged by this graph and this model key are updated or removed. Existing project elements outside that set are not targeted. Materials named `WaveHall - ...` are reused if present.

## What is created

Ten **Generic Model DirectShape mesh** elements: oval roof shell, crossing wave roof, facade panels, entrance glazing, entrance fins, wave roof piers, central skylight, skylight grid, roof panel joints, and ground floor. The default model contains 22,168 triangles. Materials include white cladding, transparent glass, aluminium, joints, and concrete.

The mesh surfaces approximate curves with facets; increase Segments for a smoother outline at greater processing cost. This is a concept envelope, not a structural design or a fully detailed building. Components are not native Revit roofs, walls, floors, structural framing, or curtain systems. The single-surface skylight has no glazing thickness. It does not include rooms, doors, foundations, reinforcement, connections, or fabrication details. Revit mesh cut/section and quantity behaviour differs from native solid building elements. Edit the form through Dynamo; use it as a reference when developing native BIM elements.

## Validation performed here

Six automated checks pass: exact default/alternate bounds, finite nondegenerate triangles, closed-component mesh edge topology and winding, reproducibility, invalid-input rejection, and graph wiring/embedded Python syntax. The preview is rendered directly from the same geometry functions used by the Dynamo node.

**Not tested:** loading or running this graph in Dynamo/Revit 2026, Revit tessellation acceptance, material appearance in Revit, or repeat-run API behaviour. The cloud machine does not have Revit or Dynamo installed. The preview is an offline geometry illustration, not a screenshot of Revit.

## Source files

The `.dyn` file is self-contained. The following are included for editing and inspection:

- `wave_geometry.py`: dependency-free geometric construction in metres.
- `revit_node.py`: Revit API creation/update adapter.
- `tools/build_graph.py`: embeds both modules in the graph.
- `tests/test_model.py`: offline geometry and graph checks.
- `tools/preview.py`: optional preview renderer using NumPy and Matplotlib.

From the repository directory, regenerate with `python tools/build_graph.py`, then validate with `python -m unittest discover -s tests -v`. Run `python tools/preview.py` to regenerate the optional image.
