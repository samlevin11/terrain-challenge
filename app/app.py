import json
from flask import Flask, render_template, request, Response
import psycopg2

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/clip_dem', methods=['POST'])
def clip_dem():
    aoi_geojson_text = json.dumps(request.json)
    dem = run_clip_query(
        aoi_geojson_text,
        'SELECT ST_AsTIFF(clip_dem(%s))'
    )
    return Response(dem, content_type='image/tiff')


@app.route('/clip_slope', methods=['POST'])
def clip_slope():
    aoi_geojson_text = json.dumps(request.json)
    slope = run_clip_query(
        aoi_geojson_text,
        'SELECT ST_AsTIFF(clip_slope(%s))'
    )
    return Response(slope, content_type='image/tiff')


@app.route('/clip_aspect', methods=['POST'])
def clip_aspect():
    aoi_geojson_text = json.dumps(request.json)
    aspect = run_clip_query(
        aoi_geojson_text,
        'SELECT ST_AsTIFF(clip_aspect(%s))'
    )
    return Response(aspect, content_type='image/tiff')


def run_clip_query(aoi_geojson_text, terrain_query):
    # Establish connection to terrain database
    conn = psycopg2.connect(
        host='localhost',
        port='5432',
        dbname='terrain',
        user='user',
        password='password'
    )
    cursor = conn.cursor()

    # Use the provided terrain_query string to call raster clipping functions
    # Returns a TIFF byte array
    cursor.execute(
        terrain_query,
        [aoi_geojson_text]
    )
    tiff_bytea = cursor.fetchone()[0]
    print(tiff_bytea)

    # Close the connection
    cursor.close()
    conn.close()

    # return TIFF
    return tiff_bytea


if __name__ == '__main__':
    app.run(debug=True)
