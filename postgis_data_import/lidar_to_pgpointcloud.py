import os
import json
import pdal
import time

start = time.perf_counter()

print('\n--------IMPORTING LIDAR TO POSTGIS POINT CLOUD--------')

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
            "connection": "host='localhost' dbname='terrain' user='user' password='password' port='5432'",
            "table": "pointcloud",
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