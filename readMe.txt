========================================================================
                  PRECISION GIS LAYOUT ENGINE - USER MANUAL
========================================================================

1. APPLICATION INTERFACE OVERVIEW
------------------------------------------------------------------------
The interface is divided into two primary sections designed for seamless
drafting:

* Left Sidebar (Control Panel): Houses your active creation toolkits,
  fine-tuning adjustments, drawing label inputs, configuration
  management dropdowns, and export pipelines.
* Right Panel (Interactive Map Canvas): Your visual drawing space
  supporting full zoom adjustments up to level 22 and multi-layered
  map tiles.


2. SETTING UP YOUR BACKGROUND LAYER
------------------------------------------------------------------------
Before drawing, choose the background map layer that best fits your
workflow using the layer controller in the top-right corner of the map
view:

1. Normal Map: A clean vector road map ideal for establishing regional
   layouts and referencing street infrastructure.
2. Satellite (Clean Canvas): Pure high-resolution aerial imagery
   completely free of text overlay, roads, or labels. Excellent for
   tracing buildings and natural geography.
3. Satellite + Labels & Shops (Default): A hybrid aerial view
   displaying roads, place-of-interest labels, and business locations.
   Use this mode to align shapes with exact commercial properties.

*Note: Regardless of which layer you use to draft, all map tiles are
automatically stripped during PDF generation to leave a perfectly
clean canvas.*


3. SHAPE CREATION TOOLKIT
------------------------------------------------------------------------
The Drawing Layer Tools panel at the top left lets you construct three
types of vector geometries:

* Draw Custom Polygon: Click to place consecutive corner points to
  outline complex, multi-sided perimeters. Click the starting node
  again to close and complete the area.
* Draw Box / Rectangle: Click and hold, then drag diagonally to create
  standard four-sided enclosures.
* Draw Line: Click to create sequential paths or linear segments.
  Double-click on your final vertex point to finalize the route.


4. PRECISION EDITING & FINE-TUNING MATRIX
------------------------------------------------------------------------
When you select an existing drawn shape on your map (indicated by a
yellow dashed outline), the Precision Editor Matrix unlocks to give you
advanced transformation options:

* Label Text: Type text directly into this field. The description will
  immediately bind to the geographic center of your shape as a permanent
  white floating label with a high-contrast text shadow. Clear the
  input box to remove the text.
* Rotation Angle: Adjust the slider from 0 to 360 degrees to spin the
  selected shape around its geographic midpoint. This allows you to
  effortlessly align structural layouts with angled property lines.
* Scale Modifier: Adjust the scale slider from 50% to 200% to shrink
  or expand your active shape globally without altering its core
  proportions or aspect ratio.
* Nudge Positioning: Click the directional grid buttons (Up, Down,
  Left, Right) to shift your shape by precise, micro-coordinate
  intervals (0.00002 degrees per click). This enables perfect alignment
  without needing to drag shapes manually with a mouse cursor.


5. HOTKEYS AND KEYBOARD SHORTCUTS
------------------------------------------------------------------------
Boost your efficiency by keeping your hands on the keyboard during
drawing sessions:

* Ctrl + Z (While actively drawing): Erases the last vertex or point
  you placed. If you accidentally misclick a corner while halfway
  through a complex polygon or long line, hit Ctrl + Z to erase that
  specific node and keep drawing.
* Ctrl + Z (While idle / not drawing): Acts as a global undo action,
  deleting the last completely finished shape from your canvas stack.
* Delete or Backspace: Removes whichever completed shape is currently
  selected (highlighted in yellow).
* Ctrl + S: Instantly brings up the Save Workspace Layout modal prompt.


6. SAVING AND LOADING PROJECTS
------------------------------------------------------------------------
The application features local file persistence so you never lose your
progress.

Saving Your Current Layout (Ctrl + S):
1. Press Ctrl + S on your keyboard.
2. A custom popup window will appear asking you to name your workspace.
3. Enter a descriptive filename (e.g., Site_Plan_Phase_1) and click
   "Save Map".
4. Your vector geometries and custom labels are securely saved into a
   local .json file in the application's root directory.

Loading a Past Project:
1. Look at section "3. Load Workspace Menu" in the sidebar.
2. Click the dropdown menu labeled "Select Saved Map Configuration".
3. Select your desired filename from the list.
4. The workspace will automatically clear its current layers and
   populate the saved layout with its exact dimensions, colors,
   rotations, scales, and text labels.


7. EXPORTING TO BLUEPRINT PDF
------------------------------------------------------------------------
Once your project is ready for submission, archiving, or sharing,
click the blue "Export Drawing to PDF" button at the bottom of the
sidebar.

How the background isolation works:
1. The application automatically deselects any active shapes to hide
   helper outlines.
2. It programmatically strips away the active Google Maps or
   OpenStreetMap tile layer.
3. It takes a clean snapshot of only your custom drawn vectors and
   their labels against a sterile white backdrop.
4. The engine compiles this into a professional, high-fidelity
   landscape A4 layout PDF named 'drawn_canvas_blueprint.pdf' in your
   app directory, perfectly isolated from external map clutter.