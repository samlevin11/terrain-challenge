import os
import psycopg2
from osgeo import gdal, osr
import subprocess
import time

# PostGIS DB connection details
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    dbname="terrain",
    user="user",
    password="password"
)
cursor = conn.cursor()

# Establish path to the raster to import
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
raster_name = 'USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_FilledDEM.tif'
raster_path = os.path.join(data_dir, raster_name)
print(f'RASTER PATH: {raster_path}')

# Open raster with GDAL and get WKT projection info
ds = gdal.Open(raster_path)
wkt = ds.GetProjection() 
# Use OGR to 
srs=osr.SpatialReference()
srs.ImportFromWkt(wkt)
print(f'SRS----\n{srs}')

srid = srs.GetAuthorityCode('PROJCS')
auth_name = srs.GetAuthorityName('PROJCS')
print(f'{auth_name}: {srid}')

# raster2pgsql -c -s 6342 -F -I -C data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_FilledDEM.tif public.filleddem
sql = subprocess.check_output([
    'raster2pgsql', '-c', '-s', '6342', '-F', '-I', raster_path, 'public.filleddem'
])

cursor.execute(sql.decode('utf-8'))
conn.commit()

cursor.close()
conn.close()