// Initialize the Leaflet map
const map = L.map('map').setView([41.23133, -105.38772], 15);

// Add OpenStreetMap and ESRI World Imagery base maps as tile layers
const osmBaseLayer = L.tileLayer(
    'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
        maxZoom: 19,
        attribution:
            '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }
);
osmBaseLayer.addTo(map);

const esriImageryLayer = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
);
esriImageryLayer.addTo(map);

const layerControl = L.control
    .layers(
        (baselayers = {
            'ESRI World Imagery': esriImageryLayer,
            'Open Street Map': osmBaseLayer,
        })
    )
    .addTo(map);

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

let layer;

const clipTerrainButton = document.getElementById('clip-terrain-button');
console.log('GET AOI BUTTON', clipTerrain);
clipTerrainButton.disabled = true;

map.on('pm:create', (e) => {
    // console.log('Shape created:', e, e.layer.toGeoJSON());
    layer = e.layer;

    map.pm.addControls({
        drawPolygon: false,
        drawRectangle: false,
        editMode: true,
        dragMode: true,
        removalMode: true,
    });

    clipTerrainButton.disabled = false;

    layerControl.addOverlay(layer, 'Area of Interest');
});

map.on('pm:remove', (e) => {
    // console.log('Shape removed:', e, e.layer.toGeoJSON());
    layer = null;

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
    geojson = layer.toGeoJSON().geometry;
    console.log('AOI GEOJSON', geojson);

    const dem_tiff = fetch_clipped('clip_dem', geojson);
    addTiffToMap(dem_tiff);

    const slope_tiff = fetch_clipped('clip_slope', geojson);
    addTiffToMap(slope_tiff);

    const aspect_tiff = fetch_clipped('clip_aspect', geojson);
    addTiffToMap(aspect_tiff);
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

function addTiffToMap(tiff) {
    tiff.then((response) => response.arrayBuffer()).then((arrayBuffer) => {
        parseGeoraster(arrayBuffer).then((georaster) => {
            console.log('georaster:', georaster);

            const layer = new GeoRasterLayer({
                georaster: georaster,
            });
            layer.addTo(map);

            map.fitBounds(layer.getBounds());

            layerControl.addOverlay(layer, 'RASTER');
        });
    });
}
