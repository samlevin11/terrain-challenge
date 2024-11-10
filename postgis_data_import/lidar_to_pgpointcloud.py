import os
import json
from dotenv import load_dotenv
import pdal
import time

start = time.perf_counter()

print('\n--------IMPORTING LIDAR TO POSTGIS POINT CLOUD--------')

# Load environment variables from .env file
load_dotenv()

host = os.getenv('POSTGRES_HOST')
dbname = os.getenv('POSTGRES_DB')
user = os.getenv('POSTGRES_USER')
password = os.getenv('POSTGRES_PASSWORD')
port = os.getenv('POSTGRES_PORT')

data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
laz_path = os.path.join(data_dir, 'USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640.laz')

pipeline_config = {
    "pipeline": [
        {
            "type": "readers.las",
            "filename": laz_path,
            "spatialreference": "EPSG:6342",
            "compression": "laszip"
        },
        {
            "type": "filters.chipper",
            "capacity": 400
        },
        {
            "type": "writers.pgpointcloud",
            "connection": f"host='{host}' dbname='{dbname}' user='{user}' password='{password}' port='{port}'",
            "table": "pointcloud_data",
            "srid": "6342",
            "overwrite": "true"
        }
    ]
}
pipeline_json = json.dumps(pipeline_config)

print('executing PDAL pipeline, importing LAZ to PostGIS')
pipeline = pdal.Pipeline(pipeline_json)
count = pipeline.execute()


print(f'POINT CLOUD IMPORT TIME: {round(time.perf_counter() - start)} seconds')
