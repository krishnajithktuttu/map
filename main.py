import http.server
import socketserver
import threading
import json
import os
import glob
import webview

PORT = 8080

# --- Clean HTML/JS Interface Engine with Full Persistent Features ---
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
        #sidebar { width: 320px; background: #2c3e50; color: white; padding: 20px; box-shadow: 2px 0 10px rgba(0,0,0,0.3); display: flex; flex-direction: column; gap: 15px; z-index: 3000; overflow-y: auto; }
        #map { flex: 1; height: 100%; z-index: 1; background: #ffffff !important; } 

        /* UI Components */
        h3 { margin-top: 0; border-bottom: 2px solid #34495e; padding-bottom: 8px; color: #1abc9c; }
        .tool-group { display: flex; flex-direction: column; gap: 8px; margin-bottom: 15px; }
        button { background: #34495e; color: white; border: none; padding: 10px 14px; border-radius: 4px; cursor: pointer; font-weight: bold; text-align: left; transition: 0.2s; }
        button:hover { background: #1abc9c; }
        .active-tool { background: #1abc9c !important; }

        .control-label { font-size: 13px; font-weight: bold; margin-bottom: 4px; display: block; color: #bdc3c7; }
        input[type=range] { width: 100%; margin-bottom: 10px; accent-color: #1abc9c; }
        input[type=text], select { width: 100%; padding: 8px; background: #34495e; color: white; border: 1px solid #1abc9c; border-radius: 4px; box-sizing: border-box; margin-bottom: 10px; }

        .move-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; width: 150px; margin: 0 auto; }
        .move-btn { text-align: center; padding: 8px; background: #34495e; }

        /* Custom Label Tooltip Styles */
        .shape-label-tooltip {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #ffffff !important;
            font-weight: bold !important;
            font-size: 14px !important;
            text-shadow: 1px 1px 2px #000, -1px -1px 2px #000;
            pointer-events: none !important;
        }

        /* Modal popup overlay */
        .modal { display: none; position: fixed; z-index: 4000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); align-items: center; justify-content: center; }
        .modal-content { background: #2c3e50; padding: 25px; border-radius: 6px; border: 2px solid #1abc9c; width: 350px; color: white; }
        .modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 15px; }
        .modal-btn { padding: 8px 16px; border-radius: 4px; border: none; font-weight: bold; cursor: pointer; }
        .modal-save { background: #1abc9c; color: white; }
        .modal-cancel { background: #7f8c8d; color: white; }
    </style>
</head>
<body>

<div id="save-modal" class="modal">
    <div class="modal-content">
        <h4 style="margin-top:0; color:#1abc9c;">Create New Map File</h4>
        <label class="control-label">Enter Map Name</label>
        <input type="text" id="save-map-name" placeholder="E.g., Site Blueprint A">
        <div class="modal-actions">
            <button class="modal-btn modal-cancel" onclick="closeSaveModal()">Cancel</button>
            <button class="modal-btn modal-save" onclick="confirmModalSave()">Create Map</button>
        </div>
    </div>
</div>

<div id="app-container">
    <div id="sidebar">
        <h3>1. Drawing Layer Tools</h3>
        <div class="tool-group">
            <button id="btn-poly" onclick="startDraw('polygon')">Draw Custom Polygon</button>
            <button id="btn-rect" onclick="startDraw('rectangle')">Draw Box / Rectangle</button>
            <button id="btn-line" onclick="startDraw('polyline')">Draw Line</button>
        </div>

        <h3>2. Precision Editor Matrix</h3>
        <div id="editor-controls" style="opacity: 0.4; pointer-events: none;">
            <div>
                <span class="control-label">Label Text</span>
                <input type="text" id="shape-label" placeholder="Type shape label here..." oninput="updateShapeLabel()">
            </div>
            <div>
                <span class="control-label">Rotation Angle (0 - 360)</span>
                <input type="range" id="slide-rotate" min="0" max="360" value="0" oninput="transformActiveShape()">
            </div>
            <div>
                <span class="control-label">Scale Modifier</span>
                <input type="range" id="slide-scale" min="50" max="200" value="100" oninput="transformActiveShape()">
            </div>
            <div>
                <span class="control-label" style="text-align:center; margin-bottom:8px;">Nudge Positioning</span>
                <div class="move-grid">
                    <div></div><button class="move-btn" onclick="nudgeShape('up')">Up</button><div></div>
                    <button class="move-btn" onclick="nudgeShape('left')">Left</button><div></div><button class="move-btn" onclick="nudgeShape('right')">Right</button>
                    <div></div><button class="move-btn" onclick="nudgeShape('down')">Down</button><div></div>
                </div>
            </div>
        </div>

        <h3>3. Workspace Options</h3>
        <div class="tool-group">
            <button onclick="openSaveModal()" style="background: #27ae60; text-align: center;">Add New Map</button>
        </div>
        <div>
            <label class="control-label">Select Saved Map Configuration</label>
            <select id="load-menu-select" onchange="triggerLoadMap()">
                <option value="">-- No Active Layout Loaded --</option>
            </select>
        </div>

        <button onclick="exportDrawingToPDF()" style="background: #2980b9; text-align: center; margin-top: auto;">Export Drawing to PDF</button>
        <button onclick="clearMap()" style="background: #e74c3c; text-align: center;">Clear Workspace</button>
    </div>

    <div id="map"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>
<script src="https://unpkg.com/leaflet-simple-map-screenshoter"></script>

<script>
    const normalMap = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 22, maxNativeZoom: 19, attribution: '© OpenStreetMap', crossOrigin: true
    });

    const satelliteCleanMap = L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
        maxZoom: 22, maxNativeZoom: 20, attribution: '© Google Imagery', crossOrigin: true
    });

    const satelliteHybridMap = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
        maxZoom: 22, maxNativeZoom: 20, attribution: '© Google Hybrid', crossOrigin: true
    });

    const map = L.map('map', { 
        zoomControl: true, maxZoom: 22, layers: [satelliteHybridMap]
    }).setView([12.5079, 74.9890], 18);

    const baseLayers = {
        "Normal Map": normalMap,
        "Satellite (Clean Canvas)": satelliteCleanMap,
        "Satellite + Labels & Shops": satelliteHybridMap
    };
    L.control.layers(baseLayers, null, { position: 'topright', collapsed: false }).addTo(map);

    const screenshoter = L.simpleMapScreenshoter({
        hidden: true, cropImageByInnerWH: true
    }).addTo(map);

    const drawnItems = new L.FeatureGroup().addTo(map);
    let shapeOrderStack = [];
    let activeDrawHandler = null;
    let selectedLayer = null;
    let baseCoordinates = null; 
    let currentLoadedMapName = ""; 

    window.addEventListener('pywebviewready', function() {
        refreshLoadMenu();
    });

    function refreshLoadMenu() {
        pywebview.api.list_saved_maps().then(function(response) {
            const selectEl = document.getElementById('load-menu-select');
            selectEl.innerHTML = '<option value="">-- No Active Layout Loaded --</option>';
            response.forEach(function(fileName) {
                const opt = document.createElement('option');
                opt.value = fileName;
                const baseName = fileName.replace('.json', '');
                opt.textContent = baseName;
                selectEl.appendChild(opt);

                if(baseName === currentLoadedMapName) {
                    selectEl.value = fileName;
                }
            });
        });
    }

    function triggerLoadMap() {
        const fileTarget = document.getElementById('load-menu-select').value;
        if (!fileTarget) {
            currentLoadedMapName = "";
            clearMap();
            return;
        }

        pywebview.api.load_gis_layer(fileTarget).then(function(geojsonStr) {
            if (!geojsonStr) return;
            clearMap();

            currentLoadedMapName = fileTarget.replace('.json', '');
            const data = JSON.parse(geojsonStr);
            L.geoJSON(data, {
                style: function(feature) {
                    if (feature.geometry.type === 'LineString') {
                        return { color: '#e74c3c', weight: 4 };
                    } else if (feature.properties && feature.properties.isRect) {
                        return { color: '#27ae60', fillOpacity: 0.2, weight: 3 };
                    }
                    return { color: '#9b59b6', fillOpacity: 0.3, weight: 3 };
                },
                onEachFeature: function (feature, layer) {
                    drawnItems.addLayer(layer);
                    shapeOrderStack.push(layer);
                    if (feature.properties && feature.properties.label) {
                        bindHiddenTooltip(layer, feature.properties.label);
                    }
                }
            });
        });
    }

    function bindHiddenTooltip(layer, labelText) {
        layer.shapeLabel = labelText;
    }

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

        if (layer.shapeLabel && layer.shapeLabel.trim() !== "") {
            layer.bindTooltip(layer.shapeLabel, {
                permanent: true, direction: 'center', className: 'shape-label-tooltip'
            }).openTooltip();
        }
    }

    function deselectShape() {
        if (selectedLayer) {
            let normalColor = (selectedLayer instanceof L.Polygon) ? '#9b59b6' : '#27ae60';
            if (selectedLayer instanceof L.Polyline && !(selectedLayer instanceof L.Polygon)) normalColor = '#e74c3c';
            selectedLayer.setStyle({ color: normalColor, dashArray: null });

            selectedLayer.unbindTooltip();
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
                permanent: true, direction: 'center', className: 'shape-label-tooltip'
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

        if (selectedLayer.shapeLabel && selectedLayer.shapeLabel.trim() !== "") {
            selectedLayer.openTooltip();
        }
    }

    function flattenPoints(arr) {
        return Array.isArray(arr[0]) ? flattenPoints(arr.reduce((acc, val) => acc.concat(val), [])) : arr;
    }

    function applyTransformRecursive(item, center, angleRad, scaleFactor) {
        if (Array.isArray(item)) {
            return item.map(subItem => applyTransformRecursive(subItem, center, angleRad, scaleFactor));
        }
        let lat = item.lat; let lng = item.lng;
        let x = lng - center.lng; let y = lat - center.lat;
        x *= scaleFactor; y *= scaleFactor;
        let xRot = x * Math.cos(angleRad) - y * Math.sin(angleRad);
        let yRot = x * Math.sin(angleRad) + y * Math.cos(angleRad);
        return L.latLng(center.lat + yRot, center.lng + xRot);
    }

    function nudgeShape(direction) {
        if (!selectedLayer) return;
        const offset = 0.00002; 
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

    function openSaveModal() {
        deselectShape();
        document.getElementById('save-map-name').value = '';
        document.getElementById('save-modal').style.display = 'flex';
        document.getElementById('save-map-name').focus();
    }

    function closeSaveModal() {
        document.getElementById('save-modal').style.display = 'none';
    }

    function confirmModalSave() {
        const inputName = document.getElementById('save-map-name').value.trim();
        if (!inputName) {
            alert("Please enter a valid name for your layout.");
            return;
        }
        currentLoadedMapName = inputName;
        executeSilentAutosave();
        closeSaveModal();
    }

    function executeSilentAutosave() {
        if (!currentLoadedMapName) {
            openSaveModal();
            return;
        }

        drawnItems.eachLayer(function(layer) {
            layer.feature = layer.feature || { type: "Feature", properties: {} };
            if(layer.shapeLabel) {
                layer.feature.properties.label = layer.shapeLabel;
            }
            if (layer instanceof L.Rectangle) {
                layer.feature.properties.isRect = true;
            }
        });

        const dataStr = JSON.stringify(drawnItems.toGeoJSON(), null, 4);
        pywebview.api.save_gis_layer(currentLoadedMapName, dataStr).then(function(success) {
            refreshLoadMenu();
        });
    }

    window.addEventListener('keydown', function(event) {
        if (document.activeElement === document.getElementById('shape-label') || document.activeElement === document.getElementById('save-map-name')) return;

        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
            event.preventDefault();
            deselectShape();
            executeSilentAutosave();
            return;
        }

        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') {
            event.preventDefault();
            if (activeDrawHandler && typeof activeDrawHandler.deleteLastVertex === 'function') {
                activeDrawHandler.deleteLastVertex();
            } else {
                if (shapeOrderStack.length === 0) return;
                deselectShape();
                const lastLayer = shapeOrderStack.pop();
                drawnItems.removeLayer(lastLayer);
            }
        }

        if (event.key === 'Delete' || event.key === 'Backspace') {
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

    function exportDrawingToPDF() {
        drawnItems.eachLayer(layer => layer.unbindTooltip());
        deselectShape(); 

        let activeTile = null;
        if (map.hasLayer(normalMap)) activeTile = normalMap;
        else if (map.hasLayer(satelliteCleanMap)) activeTile = satelliteCleanMap;
        else if (map.hasLayer(satelliteHybridMap)) activeTile = satelliteHybridMap;

        if (activeTile) map.removeLayer(activeTile);

        setTimeout(() => {
            screenshoter.takeScreen('image').then(base64Image => {
                if (activeTile) activeTile.addTo(map);
                pywebview.api.convert_image_to_pdf(base64Image);
            }).catch(err => {
                if (activeTile) activeTile.addTo(map);
                alert("Export pipeline failed: " + err);
            });
        }, 100); 
    }
</script>
</body>
</html>
"""


class Api:
    def save_gis_layer(self, map_name, geojson_data):
        safe_name = "".join([c for c in map_name if c.isalpha() or c.isdigit() or c in (' ', '_', '-')]).strip()
        filename = f"{safe_name}.json"
        with open(filename, "w") as f:
            f.write(geojson_data)
        print(f"Map changes updated inside profile storage layout: '{filename}'")
        return True

    def list_saved_maps(self):
        files = glob.glob("*.json")
        return sorted(files)

    def load_gis_layer(self, filename):
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return f.read()
        return ""

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

            pdf_path = "drawn_canvas_blueprint.pdf"
            pdf_canvas = canvas.Canvas(pdf_path, pagesize=landscape(A4))
            page_width, page_height = landscape(A4)

            pdf_canvas.drawImage(img_reader, 0, 0, width=page_width, height=page_height)
            pdf_canvas.save()

            print(f"Success! Canvas map blueprint cleared. Document saved to '{pdf_path}'")
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