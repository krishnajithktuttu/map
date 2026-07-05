import http.server
import socketserver
import threading
import json
import webview

PORT = 8080

# --- The Front-End Web-Interface (HTML, Leaflet Map, and Fabric Drawing Canvas) ---
HTML_MAIN = """
<!DOCTYPE html>
<html>
<head>
    <title>Live Map Layer Workbench</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; font-family: sans-serif; overflow: hidden; background: #2c3e50; }
        #app-container { display: flex; flex-direction: column; height: 100vh; }
        #toolbar { background: #2c3e50; color: white; padding: 12px; display: flex; gap: 10px; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.3); z-index: 3000; }
        button { background: #34495e; color: white; border: none; padding: 8px 14px; border-radius: 4px; cursor: pointer; font-weight: bold; transition: 0.2s; }
        button:hover { background: #1abc9c; }
        #map-wrapper { flex: 1; position: relative; width: 100%; height: 100%; }

        /* Layer 1: The Live Global Map */
        #map { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; }

        /* Layer 2: The Drawing Interaction Overlay */
        #canvas-container { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; pointer-events: none; }

        /* When drawing or editing, unlock mouse events for the front canvas */
        .interaction-active #canvas-container { pointer-events: auto; }
    </style>
</head>
<body>

<div id="app-container" class="interaction-active">
    <div id="toolbar">
        <button onclick="setMode('edit')">Interact / Move / Elongate 🖐️</button>
        <button onclick="setMode('draw-line')">Smooth Line ➖</button>
        <button onclick="setMode('draw-rect')">Rectangle ⬜</button>
        <button onclick="clearCanvas()" style="background: #e74c3c;">Clear Drawings 🧹</button>
        <button onclick="exportLayers()" style="background: #27ae60; margin-left: auto;">Export Drawings 📤</button>
    </div>

    <div id="map-wrapper">
        <div id="map"></div>
        <div id="canvas-container">
            <canvas id="drawingCanvas"></canvas>
        </div>
    </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>

<script>
    const wrapper = document.getElementById('map-wrapper');
    const canvasEl = document.getElementById('drawingCanvas');

    // Size the canvas to take up the full map screen area
    canvasEl.width = wrapper.clientWidth;
    canvasEl.height = wrapper.clientHeight;

    // 1. Initialize Global Interactive Map Layer
    const map = L.map('map', {
        zoomControl: true,
        scrollWheelZoom: true
    }).setView([12.5055, 74.9902], 16); // Centered over Kasaragod block coordinates

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(map);

    // 2. Initialize Fabric Vector Drawing Canvas
    const canvas = new fabric.Canvas('drawingCanvas', {
        width: wrapper.clientWidth,
        height: wrapper.clientHeight,
        selection: true
    });

    let isDrawing = false;
    let currentMode = 'edit';
    let startPoint = null;
    let activeObj = null;

    // Toggle between moving existing shapes or laying down new vectors
    function setMode(mode) {
        currentMode = mode;
        const container = document.getElementById('app-container');

        if (mode === 'edit') {
            // Let user pan the actual back map if clicking an empty space
            container.classList.remove('interaction-active'); 
            canvas.selection = true;
            canvas.forEachObject(obj => obj.selectable = true);
        } else {
            // Lock map panning to allow clean drawing paths
            container.classList.add('interaction-active');
            canvas.selection = false;
            canvas.forEachObject(obj => obj.selectable = false);
        }
    }

    // Capture initial mouse coordinate clicks
    canvas.on('mouse:down', function(options) {
        if (currentMode === 'edit') return;
        isDrawing = true;
        const pointer = canvas.getPointer(options.e);
        startPoint = { x: pointer.x, y: pointer.y };

        if (currentMode === 'draw-line') {
            activeObj = new fabric.Line([startPoint.x, startPoint.y, startPoint.x, startPoint.y], {
                stroke: '#e74c3c',
                strokeWidth: 4,
                strokeLineCap: 'round',
                hasControls: true
            });
        } else if (currentMode === 'draw-rect') {
            activeObj = new fabric.Rect({
                left: startPoint.x,
                top: startPoint.y,
                width: 0,
                height: 0,
                fill: 'rgba(231, 76, 60, 0.2)',
                stroke: '#e74c3c',
                strokeWidth: 3,
                hasControls: true
            });
        }
        canvas.add(activeObj);
    });

    // Handle interactive drag resize preview frames
    canvas.on('mouse:move', function(options) {
        if (!isDrawing || currentMode === 'edit') return;
        const pointer = canvas.getPointer(options.e);

        if (currentMode === 'draw-line') {
            activeObj.set({ x2: pointer.x, y2: pointer.y });
        } else if (currentMode === 'draw-rect') {
            let width = pointer.x - startPoint.x;
            let height = pointer.y - startPoint.y;
            activeObj.set({
                width: Math.abs(width),
                height: Math.abs(height),
                left: width > 0 ? startPoint.x : pointer.x,
                top: height > 0 ? startPoint.y : pointer.y
            });
        }
        canvas.renderAll();
    });

    // Snap objects directly into shape transform frameworks on release
    canvas.on('mouse:up', function() {
        if (!isDrawing) return;
        isDrawing = false;
        activeObj.setCoords();
        setMode('edit'); // Auto snap back to edit mode so shapes can immediately be adjusted
    });

    function clearCanvas() {
        canvas.clear();
    }

    function exportLayers() {
        const drawingsJson = JSON.stringify(canvas.toJSON());
        pywebview.api.save_drawing_layer(drawingsJson);
    }

    // Keep layers aligned during app window resizing
    window.addEventListener('resize', () => {
        canvas.setWidth(wrapper.clientWidth);
        canvas.setHeight(wrapper.clientHeight);
        canvas.renderAll();
    });
</script>
</body>
</html>
"""


def start_server():
    """Hosts our map application code locally to grant it internet permissions."""

    class CustomHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_MAIN.encode('utf-8'))

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        httpd.serve_forever()


class Api:
    def save_drawing_layer(self, json_data):
        parsed_data = json.loads(json_data)
        with open("extracted_map_shapes.json", "w") as f:
            json.dump(parsed_data, f, indent=4)
        print("Isolated vector drawings extracted successfully to 'extracted_map_shapes.json'!")


if __name__ == '__main__':
    # 1. Run local web server in background thread to unblock map textures
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 2. Launch desktop window targeting our local app url server
    api = Api()
    webview.create_window(
        'Live GIS Layer Workstation',
        url=f'http://localhost:{PORT}',
        js_api=api,
        width=1100,
        height=750
    )
    webview.start()