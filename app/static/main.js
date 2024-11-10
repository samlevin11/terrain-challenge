// Initialize the Leaflet map
// Centered on the center of the contiguous United States
const map = L.map('map').setView([39.833333, -98.583333], 5);

// Add OpenStreetMap base maps as tile layers
const osmBaseLayer = L.tileLayer(
    'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
        maxZoom: 19,
        attribution:
            '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }
);
osmBaseLayer.addTo(map);

// Initialize layer controls
let layerControl = L.control.layers(null, null, { collapsed: false });
layerControl.addTo(map);

// For tracking the Area of Interest layer
let aoi_layer;

// For tracking terrain rasters addedto the map
let terrain_rasters = [];

// Add and configure Geoman toolbar
// Enable polygon drawing options
map.pm.addControls({
    position: 'topleft',
    drawMarker: false,
    drawCircleMarker: false,
    drawPolyline: false,
    drawRectangle: true,
    drawPolygon: true,
    drawCircle: false,
    drawText: false,
    editMode: false,
    dragMode: false,
    removalMode: false,
    cutPolygon: false,
    rotateMode: false,
});

const clipTerrainButton = document.getElementById('clip-terrain-button');
clipTerrainButton.disabled = true;

const resetButton = document.getElementById('reset-button');
resetButton.disabled = true;

map.on('pm:create', (e) => {
    aoi_layer = e.layer;
    layerControl.addOverlay(aoi_layer, 'Area of Interest');

    map.pm.addControls({
        drawPolygon: false,
        drawRectangle: false,
        editMode: true,
        dragMode: true,
        removalMode: true,
    });

    clipTerrainButton.disabled = false;
});

map.on('pm:remove', (e) => {
    layerControl.removeLayer(aoi_layer);
    aoi_layer = null;

    map.pm.addControls({
        drawPolygon: true,
        drawRectangle: true,
        editMode: false,
        dragMode: false,
        removalMode: false,
    });

    clipTerrainButton.disabled = true;
});

// Initialize extent to terrain boundary
initializeExtent();

// Retrieve the extent of the terrain available in DB
// Add as a red boundary feature and zoom to
async function initializeExtent() {
    response = await fetch(`http://127.0.0.1:5000/terrain_extent`, {
        method: 'GET',
    });
    extent_geojson = await response.json();
    extent = L.geoJSON(extent_geojson, {
        style: () => {
            return { fill: false, stroke: true, color: '#800000' };
        },
    });
    extent.addTo(map);
    map.fitBounds(extent.getBounds());
}

async function clipByAoi() {
    // Reset to remove existing terrain results
    reset();
    // Hide AOI once after clip
    map.removeLayer(aoi_layer);
    geojson = aoi_layer.toGeoJSON().geometry;
    map.fitBounds(aoi_layer.getBounds());

    terrain_rasters = terrain_rasters.concat(
        await Promise.all([
            clipTerrain('clip_dem', geojson, 'Elevation'),
            clipTerrain('clip_slope', geojson, 'Slope'),
            clipTerrain('clip_aspect', geojson, 'Aspect'),
        ])
    );

    resetButton.disabled = false;
}

async function clipTerrain(endpoint, geojson, layerName) {
    const tiff = await fetchClipped(endpoint, geojson);
    const grLayer = await tiffToGeoRaster(tiff, layerName);
    grLayer.addTo(map);
    layerControl.addBaseLayer(grLayer, layerName);
    return grLayer;
}

function fetchClipped(endpoint, geojson) {
    return fetch(`http://127.0.0.1:5000/${endpoint}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(geojson),
    });
}

async function tiffToGeoRaster(tiff) {
    const arrayBuffer = await tiff.arrayBuffer();
    const georaster = await parseGeoraster(arrayBuffer);
    const grLayer = new GeoRasterLayer({
        georaster: georaster,
    });
    return grLayer;
}

function reset() {
    terrain_rasters.forEach((r) => {
        map.removeLayer(r);
        layerControl.removeLayer(r);
    });

    resetButton.disabled = true;
}
