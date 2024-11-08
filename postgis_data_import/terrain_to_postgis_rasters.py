import os
import glob
import psycopg2
from osgeo import gdal, osr
import subprocess
import time

start = time.perf_counter()

def get_raster_srid(raster_path): 
    # Open raster with GDAL and get WKT projection info
    ds = gdal.Open(raster_path)
    wkt = ds.GetProjection() 
    print(f'WKT {wkt}')
    # Use OGR to get the srid 
    srs=osr.SpatialReference()
    srs.ImportFromWkt(wkt)
    if srs.IsProjected:
        srid = srs.GetAuthorityCode('PROJCS')
        auth_name = srs.GetAuthorityName('PROJCS')
        print(f'PROJCS {auth_name}: {srid}')
    else:
        srid = srs.GetAuthorityCode('GEOGCS')
        auth_name = srs.GetAuthorityName('GEOGCS')
        print(f'GEOGCS {auth_name}: {srid}')
    return srid


def host_to_container_data_path(host_path, container_path):
    filename = os.path.split(host_path)[1]
    container_path = os.path.join(container_path, filename)
    return container_path


def raster_to_pgsql(container_tiff, srid):
    # Use suffix of TIFF as table name (indicates terrain raster type)
    tiff_basename = os.path.splitext(os.path.split(container_tiff)[1])[0]
    terrain_type = tiff_basename.split('_')[-1]
    out_table_name = 'public.' + terrain_type.lower()
    # -c create a new table
    # -s specify SRID
    # -F add column with file name
    # -I create GiST index
    # -C apply raster constraints
    sql = subprocess.check_output([
        'docker', 'exec', '-i', 'postgis_terrain',
        'raster2pgsql', '-c', '-s', srid, '-F', '-I', '-C', container_tiff, out_table_name
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
    srid = get_raster_srid(host_tiff)
    container_tiff = host_to_container_data_path(host_tiff, container_data_dir)
    sql = raster_to_pgsql(container_tiff, srid)
    execute_sql(sql)

print(f'RASTER IMPORT RUN TIME: {round(time.perf_counter() - start)} seconds')