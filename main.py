import http.server
import socketserver
import threading
import json
import webview

PORT = 8080

# --- Advanced HTML/JS Interface Engine with Precision Sidebars ---
HTML_MAIN = """
<!DOCTYPE html>
<html>
<head>
    <title>Precision GIS Layout Engine</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css" />

    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; font-family: sans-serif; overflow: hidden; background: #2c3e50; }
        #app-container { display: flex; height: 100vh; }

        /* Left Control Panel Panel */
        #sidebar { width: 320px; background: #2c3e50; color: white; padding: 20px; box-shadow: 2px 0 10px rgba(0,0,0,0.3); display: flex; flex-direction: column; gap: 15px; z-index: 3000; }

        /* White canvas background behind the map tiles */
        #map { flex: 1; height: 100%; z-index: 1; background: #ffffff !important; } 

        /* UI Components */
        h3 { margin-top: 0; border-bottom: 2px solid #34495e; padding-bottom: 8px; color: #1abc9c; }
        .tool-group { display: flex; flex-direction: column; gap: 8px; margin-bottom: 15px; }
        button { background: #34495e; color: white; border: none; padding: 10px 14px; border-radius: 4px; cursor: pointer; font-weight: bold; text-align: left; transition: 0.2s; }
        button:hover { background: #1abc9c; }
        .active-tool { background: #1abc9c !important; }

        .control-label { font-size: 13px; font-weight: bold; margin-bottom: 4px; display: block; color: #bdc3c7; }
        input[type=range] { width: 100%; margin-bottom: 10px; accent-color: #1abc9c; }
        input[type=text] { width: 100%; padding: 8px; background: #34495e; color: white; border: 1px solid #1abc9c; border-radius: 4px; box-sizing: border-box; margin-bottom: 10px; }

        .move-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; width: 150px; margin: 0 auto; }
        .move-btn { text-align: center; padding: 8px; background: #34495e; }

        /* Custom Label Tooltip Styles */
        .shape-label-tooltip {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #2c3e50 !important; /* Dark text for high contrast on the final white PDF canvas */
            font-weight: bold !important;
            font-size: 14px !important;
            pointer-events: none !important;
        }
    </style>
</head>
<body>

<div id="app-container">
    <div id="sidebar">
        <h3>1. Drawing Layer Tools</h3>
        <div class="tool-group">
            <button id="btn-poly" onclick="startDraw('polygon')">⬡ Draw Custom Polygon</button>
            <button id="btn-rect" onclick="startDraw('rectangle')">⬜ Draw Box / Rectangle</button>
            <button id="btn-line" onclick="startDraw('polyline')">➖ Draw Line</button>
        </div>

        <h3>2. Precision Editor Matrix</h3>
        <div id="editor-controls" style="opacity: 0.4; pointer-events: none;">
            <div>
                <span class="control-label">🏷️ Label Text</span>
                <input type="text" id="shape-label" placeholder="Type shape label here..." oninput="updateShapeLabel()">
            </div>
            <div>
                <span class="control-label">🔄 Rotation Angle ($0^\circ - 360^\circ$)</span>
                <input type="range" id="slide-rotate" min="0" max="360" value="0" oninput="transformActiveShape()">
            </div>
            <div>
                <span class="control-label">🎚️ Scale Modifier</span>
                <input type="range" id="slide-scale" min="50" max="200" value="100" oninput="transformActiveShape()">
            </div>
            <div>
                <span class="control-label" style="text-align:center; margin-bottom:8px;">🖐️ Nudge Positioning</span>
                <div class="move-grid">
                    <div></div><button class="move-btn" onclick="nudgeShape('up')">▲</button><div></div>
                    <button class="move-btn" onclick="nudgeShape('left')">◀</button><div></div><button class="move-btn" onclick="nudgeShape('right')">▶</button>
                    <div></div><button class="move-btn" onclick="nudgeShape('down')">▼</button><div></div>
                </div>
            </div>
        </div>

        <button onclick="exportDrawingToPDF()" style="background: #2980b9; text-align: center; margin-top: auto;">Export Drawing to PDF 📐</button>
        <button onclick="clearMap()" style="background: #e74c3c; text-align: center;">Clear Workspace 🧹</button>
        <button onclick="finalizeAndSave()" style="background: #27ae60; text-align: center;">Finalize & Save Boundary 💾</button>
    </div>

    <div id="map"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>
<script src="https://unpkg.com/leaflet-simple-map-screenshoter"></script>

<script>
    const map = L.map('map', { zoomControl: true }).setView([12.5055, 74.9902], 16);

    // Keep the live OpenStreetMap background tile active on your screen!
    const baseTileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap',
        crossOrigin: true
    }).addTo(map);

    const screenshoter = L.simpleMapScreenshoter({
        hidden: true,
        cropImageByInnerWH: true
    }).addTo(map);

    const drawnItems = new L.FeatureGroup().addTo(map);
    let shapeOrderStack = [];
    let activeDrawHandler = null;

    let selectedLayer = null;
    let baseCoordinates = null; 

    function startDraw(type) {
        if (activeDrawHandler) activeDrawHandler.disable();
        deselectShape();

        document.getElementById('btn-line').className = type === 'polyline' ? 'active-tool' : '';
        document.getElementById('btn-poly').className = type === 'polygon' ? 'active-tool' : '';
        document.getElementById('btn-rect').className = type === 'rectangle' ? 'active-tool' : '';

        if (type === 'polyline') {
            activeDrawHandler = new L.Draw.Polyline(map, { shapeOptions: { color: '#e74c3c', weight: 4 } });
        } else if (type === 'polygon') {
            activeDrawHandler = new L.Draw.Polygon(map, { shapeOptions: { color: '#9b59b6', fillOpacity: 0.3, weight: 3 } });
        } else if (type === 'rectangle') {
            activeDrawHandler = new L.Draw.Rectangle(map, { shapeOptions: { color: '#27ae60', fillOpacity: 0.2, weight: 3 } });
        }
        activeDrawHandler.enable();
    }

    map.on(L.Draw.Event.CREATED, function (e) {
        const layer = e.layer;
        layer.shapeLabel = ""; 
        drawnItems.addLayer(layer);
        shapeOrderStack.push(layer);

        document.getElementById('btn-line').className = '';
        document.getElementById('btn-poly').className = '';
        document.getElementById('btn-rect').className = '';
        activeDrawHandler = null;

        selectShape(layer);
    });

    drawnItems.on('click', function(e) {
        L.DomEvent.stopPropagation(e);
        selectShape(e.layer);
    });

    map.on('click', function() {
        deselectShape();
    });

    function selectShape(layer) {
        deselectShape();
        selectedLayer = layer;
        selectedLayer.setStyle({ color: '#f1c40f', dashArray: '5, 5' });
        baseCoordinates = JSON.parse(JSON.stringify(layer.getLatLngs()));

        document.getElementById('editor-controls').style.opacity = "1";
        document.getElementById('editor-controls').style.pointerEvents = "auto";

        document.getElementById('slide-rotate').value = 0;
        document.getElementById('slide-scale').value = 100;
        document.getElementById('shape-label').value = layer.shapeLabel || "";
    }

    function deselectShape() {
        if (selectedLayer) {
            let normalColor = (selectedLayer instanceof L.Polygon) ? '#9b59b6' : '#27ae60';
            if (selectedLayer instanceof L.Polyline && !(selectedLayer instanceof L.Polygon)) normalColor = '#e74c3c';
            selectedLayer.setStyle({ color: normalColor, dashArray: null });
        }
        selectedLayer = null;
        baseCoordinates = null;
        document.getElementById('editor-controls').style.opacity = "0.4";
        document.getElementById('editor-controls').style.pointerEvents = "none";
        document.getElementById('shape-label').value = "";
    }

    function updateShapeLabel() {
        if (!selectedLayer) return;
        const textVal = document.getElementById('shape-label').value;
        selectedLayer.shapeLabel = textVal;

        if (textVal.trim() === "") {
            selectedLayer.unbindTooltip();
        } else {
            selectedLayer.bindTooltip(textVal, {
                permanent: true,
                direction: 'center',
                className: 'shape-label-tooltip'
            }).openTooltip();
        }
    }

    function transformActiveShape() {
        if (!selectedLayer || !baseCoordinates) return;

        const angleDeg = parseFloat(document.getElementById('slide-rotate').value);
        const scalePct = parseFloat(document.getElementById('slide-scale').value) / 100.0;
        const angleRad = angleDeg * (Math.PI / 180.0);

        let bounds = L.latLngBounds(flattenPoints(baseCoordinates));
        let center = bounds.getCenter();

        let newLatLngs = applyTransformRecursive(baseCoordinates, center, angleRad, scalePct);
        selectedLayer.setLatLngs(newLatLngs);
        selectedLayer.redraw();
    }

    function flattenPoints(arr) {
        return Array.isArray(arr[0]) ? flattenPoints(arr.reduce((acc, val) => acc.concat(val), [])) : arr;
    }

    function applyTransformRecursive(item, center, angleRad, scaleFactor) {
        if (Array.isArray(item)) {
            return item.map(subItem => applyTransformRecursive(subItem, center, angleRad, scaleFactor));
        }
        let lat = item.lat;
        let lng = item.lng;

        let x = lng - center.lng;
        let y = lat - center.lat;

        x *= scaleFactor;
        y *= scaleFactor;

        let xRot = x * Math.cos(angleRad) - y * Math.sin(angleRad);
        let yRot = x * Math.sin(angleRad) + y * Math.cos(angleRad);

        return L.latLng(center.lat + yRot, center.lng + xRot);
    }

    function nudgeShape(direction) {
        if (!selectedLayer) return;
        const offset = 0.00005; 
        let latDel = 0, lngDel = 0;

        if (direction === 'up') latDel = offset;
        if (direction === 'down') latDel = -offset;
        if (direction === 'left') lngDel = -offset;
        if (direction === 'right') lngDel = offset;

        baseCoordinates = shiftCoordsRecursive(baseCoordinates, latDel, lngDel);
        transformActiveShape();
    }

    function shiftCoordsRecursive(item, latDel, lngDel) {
        if (Array.isArray(item)) {
            return item.map(subItem => shiftCoordsRecursive(subItem, latDel, lngDel));
        }
        return L.latLng(item.lat + latDel, item.lng + lngDel);
    }

    window.addEventListener('keydown', function(event) {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') {
            if (document.activeElement === document.getElementById('shape-label')) return;
            event.preventDefault();
            if (shapeOrderStack.length === 0) return;
            deselectShape();
            const lastLayer = shapeOrderStack.pop();
            drawnItems.removeLayer(lastLayer);
        }

        if (event.key === 'Delete' || event.key === 'Backspace') {
            if (document.activeElement === document.getElementById('shape-label')) return; 
            if (selectedLayer) {
                event.preventDefault();
                const targetIdx = shapeOrderStack.indexOf(selectedLayer);
                if (targetIdx > -1) shapeOrderStack.splice(targetIdx, 1);
                drawnItems.removeLayer(selectedLayer);
                deselectShape();
            }
        }
    });

    function clearMap() {
        if (activeDrawHandler) activeDrawHandler.disable();
        deselectShape();
        drawnItems.clearLayers();
        shapeOrderStack = [];
    }

    // --- AUTOMATIC BACKGROUND REMOVAL ACTION ONLY FOR THE SNAPSHOT ---
    function exportDrawingToPDF() {
        deselectShape(); // Clear selected outlines before taking the picture

        // 1. Temporarily strip away the background imagery tiles right before screenshotting
        map.removeLayer(baseTileLayer);

        // 2. Take the picture and immediately put the map background back
        setTimeout(() => {
            screenshoter.takeScreen('image').then(base64Image => {
                // Restore map tiles to your app screen instantly
                baseTileLayer.addTo(map);

                // Pass the clean image data directly to the Python backend PDF compiler
                pywebview.api.convert_image_to_pdf(base64Image);
            }).catch(err => {
                baseTileLayer.addTo(map); // Safety restore
                alert("Export failed: " + err);
            });
        }, 100); 
    }

    function finalizeAndSave() {
        deselectShape();
        drawnItems.eachLayer(function(layer) {
            if(layer.shapeLabel) {
                layer.feature = layer.feature || { type: "Feature", properties: {} };
                layer.feature.properties.label = layer.shapeLabel;
            }
        });
        const data = drawnItems.toGeoJSON();
        pywebview.api.save_gis_layer(JSON.stringify(data, null, 4));
    }
</script>
</body>
</html>
"""


class Api:
    def save_gis_layer(self, geojson_data):
        with open("finalized_boundary.geojson", "w") as f:
            f.write(geojson_data)
        print("Export complete! Layer saved safely to 'finalized_boundary.geojson'")

    def convert_image_to_pdf(self, base64_image_data):
        try:
            import base64
            from io import BytesIO
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader

            if "," in base64_image_data:
                base64_image_data = base64_image_data.split(",")[1]

            img_bytes = base64.b64decode(base64_image_data)
            img_buffer = BytesIO(img_bytes)
            img_reader = ImageReader(img_buffer)

            # Generate Document file (Clean blueprint layout canvas sheet)
            pdf_path = "drawn_canvas_blueprint.pdf"
            pdf_canvas = canvas.Canvas(pdf_path, pagesize=landscape(A4))
            page_width, page_height = landscape(A4)

            # Paint drawings onto vector PDF canvas
            pdf_canvas.drawImage(img_reader, 0, 0, width=page_width, height=page_height)
            pdf_canvas.save()

            print(f"Success! Canvas artwork document saved to '{pdf_path}'")
        except Exception as e:
            print(f"Backend image pipeline writing failed: {e}")


def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
        global HTML_MAIN

        class InlineHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(HTML_MAIN.encode('utf-8'))

        httpd.RequestHandlerClass = InlineHandler
        httpd.serve_forever()


if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    api = Api()
    webview.create_window('Scale-Accurate Precision GIS Studio', url=f'http://localhost:{PORT}', js_api=api, width=1200,
                          height=800)
    webview.start()