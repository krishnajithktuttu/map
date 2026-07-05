import http.server
import socketserver
import threading
import json
import os
import glob
import webview

PORT = 8080

# --- Clean HTML/JS Interface Engine with Multi-Page Vector Export ---
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
            font-family: sans-serif !important;
            font-size: 14px !important;
            text-shadow: 1px 1px 2px #000, -1px -1px 2px #000;
            pointer-events: none !important;
            white-space: nowrap !important;
            padding: 0 !important;
            margin: 0 !important;
            box-sizing: content-box !important;
        }
        .shape-label-tooltip::before {
            display: none !important;
        }

        /* Modal popup overlay */
        .modal { display: none; position: fixed; z-index: 4000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); align-items: center; justify-content: center; }
        .modal-content { background: #2c3e50; padding: 25px; border-radius: 6px; border: 2px solid #1abc9c; width: 350px; color: white; }
        .modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 15px; }
        .modal-btn { padding: 8px 16px; border-radius: 4px; border: none; font-weight: bold; cursor: pointer; }
        .modal-save { background: #1abc9c; color: white; }
        .modal-cancel { background: #7f8c8d; color: white; }

        /* Save success toast notification */
        #toast-notification {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%) translateY(20px);
            background: #27ae60;
            color: white;
            padding: 12px 26px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 14px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.35);
            z-index: 5000;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease, transform 0.3s ease;
        }
        #toast-notification.show {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }
    </style>
</head>
<body>

<div id="toast-notification">Saved successfully!</div>

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

        <button onclick="exportDrawingToVectorPDF()" style="background: #2980b9; text-align: center; margin-top: auto;">Export Drawing to PDF</button>
        <button onclick="clearMap()" style="background: #e74c3c; text-align: center;">Clear Workspace</button>
    </div>

    <div id="map"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>

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

    const drawnItems = new L.FeatureGroup().addTo(map);
    let shapeOrderStack = [];
    let activeDrawHandler = null;
    let selectedLayer = null;
    let baseCoordinates = null; 
    let currentLoadedMapName = ""; 
    let toastTimeoutHandle = null;

    window.addEventListener('pywebviewready', function() {
        refreshLoadMenu();
    });

    function showToast(message, color) {
        const toastEl = document.getElementById('toast-notification');
        toastEl.textContent = message;
        toastEl.style.background = color || '#27ae60';
        toastEl.classList.add('show');
        if (toastTimeoutHandle) clearTimeout(toastTimeoutHandle);
        toastTimeoutHandle = setTimeout(function() {
            toastEl.classList.remove('show');
        }, 2200);
    }

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

    map.on('zoomend', function() {
        if (selectedLayer && selectedLayer.shapeLabel && selectedLayer.shapeLabel.trim() !== "") {
            fitLabelToShape(selectedLayer);
        }
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
            fitLabelToShape(layer);
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
            fitLabelToShape(selectedLayer);
        }
    }

    // Computes the on-screen pixel width/height of a shape's bounding box
    function getShapePixelBounds(layer) {
        const bounds = layer.getBounds();
        const nw = map.latLngToLayerPoint(bounds.getNorthWest());
        const se = map.latLngToLayerPoint(bounds.getSouthEast());
        return {
            width: Math.abs(se.x - nw.x),
            height: Math.abs(se.y - nw.y)
        };
    }

    // Outer ring of a polygon/rectangle layer, converted to screen pixel points
    function getPolygonPixelRing(layer) {
        let ring = layer.getLatLngs();
        while (Array.isArray(ring[0])) {
            ring = ring[0];
        }
        return ring.map(function(ll) { return map.latLngToLayerPoint(ll); });
    }

    // Finds how much horizontal/vertical space is actually INSIDE the polygon
    // at the row/column that passes through its center, by ray-casting against
    // every edge. This is what a bounding-box check misses: a triangle or any
    // non-rectangular shape has a lot less usable interior than its bbox.
    function getInteriorExtentsAtCenter(ringPoints, center) {
        function extentAlong(axisIsY, fixedVal, movingVal) {
            const hits = [];
            for (let i = 0; i < ringPoints.length; i++) {
                const p1 = ringPoints[i];
                const p2 = ringPoints[(i + 1) % ringPoints.length];
                const a1 = axisIsY ? p1.y : p1.x;
                const a2 = axisIsY ? p2.y : p2.x;
                const b1 = axisIsY ? p1.x : p1.y;
                const b2 = axisIsY ? p2.x : p2.y;
                if ((a1 <= fixedVal && a2 > fixedVal) || (a2 <= fixedVal && a1 > fixedVal)) {
                    const t = (fixedVal - a1) / (a2 - a1);
                    hits.push(b1 + t * (b2 - b1));
                }
            }
            hits.sort(function(a, b) { return a - b; });
            for (let i = 0; i < hits.length - 1; i += 2) {
                if (movingVal >= hits[i] && movingVal <= hits[i + 1]) {
                    return hits[i + 1] - hits[i];
                }
            }
            if (hits.length >= 2) return hits[hits.length - 1] - hits[0];
            return 0;
        }

        return {
            width: extentAlong(true, center.y, center.x),
            height: extentAlong(false, center.x, center.y)
        };
    }

    // Shrinks the tooltip font so the label text fits inside the shape's own interior.
    // Small shapes get a small font, but the label is never hidden outright - a slightly
    // tight label on a tiny building beats no label at all.
    function fitLabelToShape(layer) {
        if (!layer.shapeLabel || layer.shapeLabel.trim() === "") return;
        const tooltip = layer.getTooltip();
        if (!tooltip) return;
        const tooltipEl = tooltip.getElement();
        if (!tooltipEl) return;

        const MIN_USABLE = 6; // smallest legible font size, in px

        let maxWidth, maxHeight;

        if (layer instanceof L.Polygon) {
            const ringPoints = getPolygonPixelRing(layer);
            const centerLatLng = (typeof layer.getCenter === 'function') ? layer.getCenter() : layer.getBounds().getCenter();
            const centerPoint = map.latLngToLayerPoint(centerLatLng);
            const extents = getInteriorExtentsAtCenter(ringPoints, centerPoint);
            maxWidth = extents.width * 0.82;
            maxHeight = extents.height * 0.6;
        } else {
            const pixelBounds = getShapePixelBounds(layer);
            maxWidth = pixelBounds.width * 0.8;
            maxHeight = pixelBounds.height * 0.5;
        }

        // Never let the box collapse to nothing - always leave room for the minimum font
        maxWidth = Math.max(maxWidth, MIN_USABLE);
        maxHeight = Math.max(maxHeight, MIN_USABLE);

        tooltipEl.style.display = 'inline-block';
        tooltipEl.style.whiteSpace = 'nowrap';
        tooltipEl.style.padding = '0';
        tooltipEl.style.margin = '0';

        // Step 1: cheap estimate via canvas text measurement to pick a starting point
        if (!fitLabelToShape._canvas) {
            fitLabelToShape._canvas = document.createElement('canvas');
        }
        const ctx = fitLabelToShape._canvas.getContext('2d');
        const refSize = 100;
        ctx.font = `bold ${refSize}px sans-serif`;
        const textWidth = ctx.measureText(layer.shapeLabel).width;

        let fontSize;
        if (textWidth > 0) {
            fontSize = Math.min((maxWidth / textWidth) * refSize, maxHeight);
        } else {
            fontSize = maxHeight;
        }
        fontSize = Math.max(MIN_USABLE, Math.min(fontSize, 22));

        tooltipEl.style.fontSize = fontSize + 'px';
        tooltipEl.style.lineHeight = fontSize + 'px';

        // Step 2: refine against the *actual* rendered box (real font metrics, no guesswork).
        // Shrink until it fits, but never go below the legible floor - a tiny building's
        // label may then sit slightly tight against the edges rather than disappear.
        let guard = 0;
        while (guard < 60 && fontSize > MIN_USABLE &&
               (tooltipEl.offsetWidth > maxWidth || tooltipEl.offsetHeight > maxHeight)) {
            fontSize -= 1;
            tooltipEl.style.fontSize = fontSize + 'px';
            tooltipEl.style.lineHeight = fontSize + 'px';
            guard++;
        }

        // In case the estimate undershot, try growing back up slightly without exceeding bounds
        guard = 0;
        while (guard < 40 && fontSize < 22 &&
               (tooltipEl.offsetWidth < maxWidth && tooltipEl.offsetHeight < maxHeight)) {
            const nextSize = fontSize + 1;
            tooltipEl.style.fontSize = nextSize + 'px';
            tooltipEl.style.lineHeight = nextSize + 'px';
            if (tooltipEl.offsetWidth > maxWidth || tooltipEl.offsetHeight > maxHeight) {
                tooltipEl.style.fontSize = fontSize + 'px';
                tooltipEl.style.lineHeight = fontSize + 'px';
                break;
            }
            fontSize = nextSize;
            guard++;
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
            fitLabelToShape(selectedLayer);
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
            if (success) {
                showToast('Saved successfully!');
            }
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

    function exportDrawingToVectorPDF() {
        deselectShape();

        drawnItems.eachLayer(function(layer) {
            layer.feature = layer.feature || { type: "Feature", properties: {} };
            if(layer.shapeLabel) layer.feature.properties.label = layer.shapeLabel;
            if (layer instanceof L.Rectangle) layer.feature.properties.isRect = true;
        });

        const bounds = map.getBounds();
        const payload = {
            geojson: drawnItems.toGeoJSON(),
            mapName: currentLoadedMapName || "Untitled_Map",
            bbox: {
                west: bounds.getWest(),
                east: bounds.getEast(),
                south: bounds.getSouth(),
                north: bounds.getNorth()
            }
        };

        pywebview.api.generate_indexed_vector_pdf(JSON.stringify(payload)).then(function(result) {
            if (result && result.success) {
                showToast('PDF exported successfully!', '#2980b9');
            } else {
                showToast('PDF export failed', '#c0392b');
            }
        });
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

    def generate_indexed_vector_pdf(self, payload_str):
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.pdfgen import canvas
            from reportlab.lib import colors

            payload = json.loads(payload_str)
            geojson = payload["geojson"]
            bbox = payload["bbox"]
            map_name = payload.get("mapName") or "Untitled_Map"

            safe_name = "".join([c for c in map_name if c.isalpha() or c.isdigit() or c in (' ', '_', '-')]).strip()
            if not safe_name:
                safe_name = "Untitled_Map"
            pdf_path = f"{safe_name}.pdf"

            # Canvas() opens the file in write mode, so an existing PDF with the
            # same name is replaced automatically.
            pdf_canvas = canvas.Canvas(pdf_path, pagesize=landscape(A4))
            page_w, page_h = landscape(A4)
            margin = 50

            def polygon_centroid(points):
                cx = sum(p[0] for p in points) / len(points)
                cy = sum(p[1] for p in points) / len(points)
                return cx, cy

            def interior_extent_at_center(points, center):
                """How much horizontal/vertical space is actually INSIDE the polygon
                at the row/column through its center — a bounding box overstates this
                for anything non-rectangular (triangles, slivers, L-shapes, etc.)."""
                cx, cy = center
                n = len(points)

                def extent_along(axis_is_y, fixed_val, moving_val):
                    hits = []
                    for i in range(n):
                        p1 = points[i]
                        p2 = points[(i + 1) % n]
                        a1 = p1[1] if axis_is_y else p1[0]
                        a2 = p2[1] if axis_is_y else p2[0]
                        b1 = p1[0] if axis_is_y else p1[1]
                        b2 = p2[0] if axis_is_y else p2[1]
                        if (a1 <= fixed_val < a2) or (a2 <= fixed_val < a1):
                            t = (fixed_val - a1) / (a2 - a1)
                            hits.append(b1 + t * (b2 - b1))
                    hits.sort()
                    for i in range(0, len(hits) - 1, 2):
                        if hits[i] <= moving_val <= hits[i + 1]:
                            return hits[i + 1] - hits[i]
                    if len(hits) >= 2:
                        return hits[-1] - hits[0]
                    return 0

                width = extent_along(True, cy, cx)
                height = extent_along(False, cx, cy)
                return width, height

            def fit_font_size(canvas_obj, text, max_width, max_height,
                               font_name="Helvetica-Bold", max_size=10.0, min_size=4.0):
                """Largest font size (in min_size..max_size) whose rendered width/height
                stay inside the given box. If the shape is too small for even min_size to
                fit cleanly, still returns min_size — a slightly tight label beats a
                missing one for small buildings."""
                size = max_size
                while size > min_size:
                    text_w = canvas_obj.stringWidth(text, font_name, size)
                    if text_w <= max_width and size <= max_height:
                        return size
                    size -= 0.5
                return min_size

            def draw_geometry(canvas_obj, draw_labels=False):
                draw_w = page_w - (2 * margin)
                draw_h = page_h - (2 * margin)
                bbox_w = bbox["east"] - bbox["west"]
                bbox_h = bbox["north"] - bbox["south"]

                def map_coords(lng, lat):
                    x = margin + ((lng - bbox["west"]) / bbox_w) * draw_w
                    y = margin + ((lat - bbox["south"]) / bbox_h) * draw_h
                    return x, y

                index = 1
                for feature in geojson.get("features", []):
                    geom = feature.get("geometry", {})
                    props = feature.get("properties", {})
                    g_type = geom.get("type")
                    coords = geom.get("coordinates", [])

                    if g_type in ["Polygon", "MultiPolygon"]:
                        color = colors.HexColor("#27ae60") if props.get("isRect") else colors.HexColor("#9b59b6")
                        canvas_obj.setStrokeColor(color)
                        canvas_obj.setLineWidth(0.25)

                        rings = coords if g_type == "Polygon" else coords[0]
                        for ring in rings:
                            path = canvas_obj.beginPath()
                            for i, pt in enumerate(ring):
                                x, y = map_coords(pt[0], pt[1])
                                if i == 0:
                                    path.moveTo(x, y)
                                else:
                                    path.lineTo(x, y)
                            path.close()
                            canvas_obj.drawPath(path, fill=0, stroke=1)

                        if draw_labels:
                            ring_pts = [map_coords(p[0], p[1]) for p in rings[0]]
                            center = polygon_centroid(ring_pts)
                            extent_w, extent_h = interior_extent_at_center(ring_pts, center)
                            # Breathing room so the digits never touch the polygon's edge
                            # (small/degenerate extents just mean the shape can't offer
                            # much room - fit_font_size falls back to a legible minimum)
                            max_w = max(extent_w * 0.8, 0.1)
                            max_h = max(extent_h * 0.6, 0.1)

                            label_text = str(index)
                            font_size = fit_font_size(canvas_obj, label_text, max_w, max_h)
                            canvas_obj.setFont("Helvetica-Bold", font_size)
                            canvas_obj.setFillColor(colors.HexColor("#2c3e50"))
                            canvas_obj.drawCentredString(center[0], center[1] - font_size * 0.35, label_text)
                        index += 1

                    elif g_type == "LineString":
                        canvas_obj.setStrokeColor(colors.HexColor("#e74c3c"))
                        canvas_obj.setLineWidth(0.25)
                        path = canvas_obj.beginPath()
                        for i, pt in enumerate(coords):
                            x, y = map_coords(pt[0], pt[1])
                            if i == 0:
                                path.moveTo(x, y)
                            else:
                                path.lineTo(x, y)
                        canvas_obj.drawPath(path, fill=0, stroke=1)

            # Page 1 & 2: Maps
            draw_geometry(pdf_canvas, draw_labels=True)
            pdf_canvas.showPage()
            draw_geometry(pdf_canvas, draw_labels=False)
            pdf_canvas.showPage()

            # Page 3+: Auto-paginated Legend
            pdf_canvas.setFont("Helvetica-Bold", 16)
            pdf_canvas.drawString(margin, page_h - 60, "Map Index Description Legend")

            y_cursor = page_h - 100
            pdf_canvas.setFont("Helvetica", 10)

            idx = 1
            for feature in geojson.get("features", []):
                if feature["geometry"]["type"] in ["Polygon", "MultiPolygon"]:
                    # Create new page if we run out of vertical space
                    if y_cursor < margin:
                        pdf_canvas.showPage()
                        y_cursor = page_h - 60

                    label = feature["properties"].get("label", "Unnamed")
                    pdf_canvas.drawString(margin, y_cursor, f"{idx}. {label}")
                    y_cursor -= 20
                    idx += 1

            pdf_canvas.save()
            print(f"PDF generated with auto-pagination: '{pdf_path}'")
            return {"success": True, "filename": pdf_path}
        except Exception as e:
            print(f"Error: {e}")
            return {"success": False, "error": str(e)}

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