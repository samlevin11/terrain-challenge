// Initialize the Leaflet map
const map = L.map('map').setView([41.23133, -105.38772], 15);

// Add OpenStreetMap base map as tile layer
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution:
        '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

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

let shape;

map.on('pm:create', (e) => {
    console.log('Shape created:', e, e.layer.toGeoJSON());
    shape = e.layer.toGeoJSON();

    map.pm.addControls({
        drawPolygon: false,
        drawRectangle: false,
        editMode: true,
        dragMode: true,
        removalMode: true,
    });
});

map.on('pm:remove', (e) => {
    console.log('Shape removed:', e, e.layer.toGeoJSON());
    shape = null;

    map.pm.addControls({
        drawPolygon: true,
        drawRectangle: true,
        editMode: false,
        dragMode: false,
        removalMode: false,
    });
});

function getAoi() {
    console.log('CLICKED!!');
    const layers = map.pm.getGeomanDrawLayers();
    const geojson = layers.map((l) => l.toGeoJSON());
    console.log('GEOJSON', geojson);
}
