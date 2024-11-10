import json
from flask import Flask, render_template, request, Response, stream_with_context
import psycopg2

app = Flask(__name__)


def get_db_connection():
    conn = psycopg2.connect(
        host='localhost',
        port='5432',
        dbname='terrain',
        user='user',
        password='password'
    )
    return conn


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/terrain_extent', methods=['POST', 'GET'])
def terrain_extent():
    # Establish connection to terrain database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Use the provided terrain_query string to call raster clipping functions
    # Returns a TIFF byte array
    cursor.execute(
        'SELECT ST_AsGeoJSON(ST_Transform(ST_MinConvexHull(rast), 4326))\
            FROM public.demfilled'
    )
    extent_geojson = cursor.fetchone()[0]

    # Close the connection
    cursor.close()
    conn.close()

    # return extent as GeoJSON text
    return extent_geojson


@app.route('/clip_dem', methods=['POST'])
def clip_dem():
    # Get GeoJSON from request body, convert to string
    aoi_geojson_text = json.dumps(request.json)
    # Use the clip_dem DB function
    # Return data as a GeoTIFF (byte array)
    dem = run_clip_query(
        aoi_geojson_text,
        'SELECT ST_AsTIFF(clip_dem(%s))'
    )
    # Stream the data back to client
    return Response(
        stream_with_context(generate(dem.tobytes())),
        content_type='image/tiff'
    )


@app.route('/clip_slope', methods=['POST'])
def clip_slope():
    # Get GeoJSON from request body, convert to string
    aoi_geojson_text = json.dumps(request.json)
    # Use the clip_slope DB function
    # Return data as a GeoTIFF (byte array)
    slope = run_clip_query(
        aoi_geojson_text,
        'SELECT ST_AsTIFF(clip_slope(%s))'
    )
    # Stream the data back to client
    return Response(
        stream_with_context(generate(slope.tobytes())),
        content_type='image/tiff'
    )


@app.route('/clip_aspect', methods=['POST'])
def clip_aspect():
    # Get GeoJSON from request body, convert to string
    aoi_geojson_text = json.dumps(request.json)
    # Use the clip_aspect DB function
    # Return data as a GeoTIFF (byte array)
    aspect = run_clip_query(
        aoi_geojson_text,
        'SELECT ST_AsTIFF(clip_aspect(%s))'
    )
    # Stream the data back to client
    return Response(
        stream_with_context(generate(aspect.tobytes())),
        content_type='image/tiff'
    )


# Chunk the byte array for return to the client
# Allows the client to start receiving data sooner
# Significantly improves performance
def generate(bytes):
    chunk_size = 8192
    for i in range(0, len(bytes), chunk_size):
        yield bytes[i:i + chunk_size] 


def run_clip_query(aoi_geojson_text, terrain_query):
    # Establish connection to terrain database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Use the provided terrain_query string to call raster clipping functions
    # Returns a TIFF byte array
    cursor.execute(
        terrain_query,
        [aoi_geojson_text]
    )
    tiff_bytea = cursor.fetchone()[0]

    # Close the connection
    cursor.close()
    conn.close()

    # return TIFF
    return tiff_bytea


if __name__ == '__main__':
    app.run(debug=True)
