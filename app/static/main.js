// Initialize the Leaflet map
const map = L.map('map').setView([41.23133, -105.38772], 15);

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
// Added to map once AOI is created
let layerControl;

// For tracking the Area of Interest
let aoi_layer;

let dem_layer;
let slope_layer;
let aspect_layer;

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
console.log('GET AOI BUTTON', clipByAoi);
clipTerrainButton.disabled = true;

map.on('pm:create', (e) => {
    layerControl = L.control.layers();

    aoi_layer = e.layer;

    map.pm.addControls({
        drawPolygon: false,
        drawRectangle: false,
        editMode: true,
        dragMode: true,
        removalMode: true,
    });

    clipTerrainButton.disabled = false;

    layerControl.addOverlay(aoi_layer, 'Area of Interest');
    layerControl.addTo(map);
});

map.on('pm:remove', (e) => {
    aoi_layer = null;

    map.pm.addControls({
        drawPolygon: true,
        drawRectangle: true,
        editMode: false,
        dragMode: false,
        removalMode: false,
    });

    clipTerrainButton.disabled = true;

    layerControl.remove();
    layerControl = null;

    map.removeLayer(dem_layer);
    map.removeLayer(slope_layer);
    map.removeLayer(aspect_layer);
});

async function clipByAoi() {
    geojson = aoi_layer.toGeoJSON().geometry;
    console.log('AOI GEOJSON', geojson);
    map.fitBounds(aoi_layer.getBounds());

    [dem_layer, slope_layer, aspect_layer] = await Promise.all([
        clipTerrain('clip_dem', geojson, 'Elevation'),
        clipTerrain('clip_slope', geojson, 'Slope'),
        clipTerrain('clip_aspect', geojson, 'Aspect'),
    ]);
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
