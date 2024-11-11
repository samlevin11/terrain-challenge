import os
import time
import json
from dotenv import load_dotenv
import pdal

def lidar_to_pgpointcloud(laz_file, srid):
    start = time.perf_counter()

    print('\n--------IMPORTING LIDAR TO POSTGIS POINT CLOUD--------')

    # Load environment variables from .env file
    load_dotenv()

    host = os.getenv('POSTGRES_HOST')
    dbname = os.getenv('POSTGRES_DB')
    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')
    port = os.getenv('POSTGRES_PORT')

    # PDAL pipeline configuration
    # User LAS reader and pgPointCloud Writer
    # Use chipper to split points into patches of ~400 points
    # Establish PostGIS DB connection for writer
    pipeline_config = {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": laz_file,
                "spatialreference": f"EPSG:{srid}",
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
                "srid": f"{srid}",
                "overwrite": "true"
            }
        ]
    }
    pipeline_json = json.dumps(pipeline_config)

    print('executing PDAL pipeline, importing LAZ to PostGIS')
    pipeline = pdal.Pipeline(pipeline_json)
    pipeline.execute()

    print(f'POINT CLOUD IMPORT TIME: {round(time.perf_counter() - start)} seconds')


if __name__ == '__main__':
    lidar_to_pgpointcloud(
        os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data')),
            'USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640.laz'
        ),
        6342
    )
