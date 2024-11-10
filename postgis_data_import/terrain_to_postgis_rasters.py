import os
import glob
import subprocess
import time
import psycopg2
from osgeo import gdal

start = time.perf_counter()

print('\n--------IMPORTING TERRAIN RASTERS TO POSTGIS--------')

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
        host="localhost",
        port="5432",
        dbname="terrain",
        user="user",
        password="password"
    )
    cursor = conn.cursor()
    # Execute and commit SQL
    cursor.execute(sql.decode('utf-8'))
    conn.commit()
    # Close cursor and connection
    cursor.close()
    conn.close()


# Establish path to the host data folder
host_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
# Establish path to the container data folder
container_data_dir = '/data'

# List GeoTIFFs in the host folder
host_tiffs = glob.glob(os.path.join(host_data_dir,'*.tif'))
print(f'HOST GEOTIFFs({len(host_tiffs)}): {host_tiffs}')

for host_tiff in host_tiffs:
    print('----------------\n' + host_tiff)
    srid = get_raster_srid(host_tiff)
    container_path = host_to_container_data_path(host_tiff, container_data_dir)
    rast_to_db_sql = raster_to_pgsql(container_path, srid)
    execute_sql(rast_to_db_sql)

print(f'RASTER IMPORT RUN TIME: {round(time.perf_counter() - start)} seconds')
