import json
from flask import Flask, render_template, request
import psycopg2

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/clip_terrain', methods=['POST'])
def clip_terrain():
    print('CLIP TERRAIN!!', request)
    aoi_geojson_text = json.dumps(request.json)
    print('AOI GEOJSON TEXT')
    print(aoi_geojson_text)

    run_clip_query(aoi_geojson_text)

    return 'TEMP RETURN'


def run_clip_query(aoi_geojson_text): 
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        dbname="terrain",
        user="user",
        password="password"
    )
    cursor = conn.cursor()

    cursor.execute(
        "SELECT dem_tiff, slope_tiff, aspect_tiff FROM clip_terrain(%s)",
        [aoi_geojson_text]
    )
    dem, slope, aspect = cursor.fetchone()


if __name__ == '__main__':
    app.run(debug=True)
