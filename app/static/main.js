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
let layerControl = L.control.layers();

// For tracking the Area of Interest
let aoi_layer;

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
console.log('GET AOI BUTTON', clipTerrain);
clipTerrainButton.disabled = true;

map.on('pm:create', (e) => {
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
});

async function clipTerrain() {
    geojson = aoi_layer.toGeoJSON().geometry;
    console.log('AOI GEOJSON', geojson);
    map.fitBounds(aoi_layer.getBounds());

    const dem_tiff = clip_terrain('clip_dem', geojson, 'Elevation');
    const slope_tiff = clip_terrain('clip_slope', geojson, 'Slope');
    const aspect_tiff = clip_terrain('clip_aspect', geojson, 'Aspect');
}

async function clip_terrain(endpoint, geojson, layerName) {
    const tiff = await fetch_clipped(endpoint, geojson);
    const grLayer = await tiffToGeoRaster(tiff, layerName);

    grLayer.addTo(map);
    layerControl.addBaseLayer(grLayer, layerName);
}

function fetch_clipped(endpoint, geojson) {
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
    console.log('georaster:', georaster);
    const grLayer = new GeoRasterLayer({
        georaster: georaster,
    });
    return grLayer;
}
