import os
import subprocess
import time
from dotenv import load_dotenv
import psycopg2
from osgeo import gdal

# Load environment variables from .env file
load_dotenv()

def get_raster_srid(raster_path):
    # Open raster with GDAL and get WKT projection info
    ds = gdal.Open(raster_path)
    # Get the OSR Spatial Reference
    srs = ds.GetSpatialRef()
    # Return SRID based on whether spatial reference is projected or geographic
    if srs.IsProjected:
        srid_code = srs.GetAuthorityCode('PROJCS')
        auth_name = srs.GetAuthorityName('PROJCS')
        print(f'PROJCS {auth_name}: {srid_code}')
    else:
        srid_code = srs.GetAuthorityCode('GEOGCS')
        auth_name = srs.GetAuthorityName('GEOGCS')
        print(f'GEOGCS {auth_name}: {srid_code}')
    return srid_code


def host_to_container_data_path(host_tiff_path, container_data_path):
    # Convert path of host TIFF to it's container path
    # ../data directory available in container via a mounted volume
    filename = os.path.split(host_tiff_path)[1]
    container_data_path = os.path.join(container_data_path, filename)
    return container_data_path


def raster_to_pgsql(container_tiff, srid_code):
    # Use suffix of TIFF as table name
    # Indicates terrain raster type (DEM, Aspect, Slope)
    tiff_basename = os.path.splitext(os.path.split(container_tiff)[1])[0]
    terrain_type = tiff_basename.split('_')[-1]
    out_table_name = 'public.' + terrain_type.lower()
    # Connect to the container terminal and run raster2pgsql
    # Since this program may not be available on the host machine
    # It can more reliably be accessed via the container
    # -c create a new table
    # -s specify SRID
    # -F add column with file name
    # -I create GiST index
    # -C apply raster constraints
    sql = subprocess.check_output([
        'docker', 'exec', '-i', 'postgis_terrain',
        'raster2pgsql', '-c', '-s', srid_code, '-F', '-I', '-C', container_tiff, out_table_name
    ])
    return sql


def execute_sql(sql):
    # Establish PostGIS DB connection
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    cursor = conn.cursor()
    # Execute and commit SQL
    cursor.execute(sql.decode('utf-8'))
    conn.commit()
    # Close cursor and connection
    cursor.close()
    conn.close()


def terrain_to_postgis_rasters(terrain_geotiffs):
    start = time.perf_counter()

    print('\n--------IMPORTING TERRAIN RASTERS TO POSTGIS--------')
    print(f'GEOTIFFs({len(terrain_geotiffs)}): {terrain_geotiffs}')

    # Establish path to the container data folder
    container_data_dir = '/data'

    for host_geotiff in terrain_geotiffs:
        print('----------------\n' + host_geotiff)
        srid = get_raster_srid(host_geotiff)
        container_path = host_to_container_data_path(host_geotiff, container_data_dir)
        rast_to_db_sql = raster_to_pgsql(container_path, srid)
        execute_sql(rast_to_db_sql)

    print(f'RASTER IMPORT RUN TIME: {round(time.perf_counter() - start)} seconds')


if __name__ == '__main__':
    terrain_to_postgis_rasters(
        [
            os.path.join(
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data')),
                'USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_DEMRaw.tif'
            ),
            os.path.join(
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data')),
                'USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_DEMFilled.tif'
            ),
            os.path.join(
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data')),
                'USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_Slope.tif'
            ),
            os.path.join(
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data')),
                'USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_Aspect.tif'
            ),
        ]
    )
