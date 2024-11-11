import os
import time
from terrain_processing.download_lidar import download_lidar
from terrain_processing.lidar_to_terrain_rasters import lidar_to_terrain_rasters
from postgis_data_import.lidar_to_pgpointcloud import lidar_to_pgpointcloud
from postgis_data_import.terrain_to_postgis_rasters import terrain_to_postgis_rasters

start = time.perf_counter()

# URL to the LAZ file
# Metadata links
# https://www.sciencebase.gov/catalog/item/62b6b4a2d34e8f4977cc320a
# https://prd-tnm.s3.amazonaws.com/index.html?prefix=StagedProducts/Elevation/metadata/WY_SouthCentral_2020_D20/WY_SouthCentral_3_2020
laz_url = 'https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/WY_SouthCentral_2020_D20/WY_SouthCentral_3_2020/LAZ/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640.laz'

# SRID of the LIDAR data, as specified in product metadata
# https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/metadata/WY_SouthCentral_2020_D20/WY_SouthCentral_3_2020/reports/vendor_provided_xml/WY_South_Central_3_2020_D20_Classified_Point_Cloud_Metadata_222437.xml
# EPSG:6342 (NAD83(2011) / UTM zone 13N)
srid = 6342

# Define the shared volume directory to download the LAZ file to
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))

# Download LIDAR LAZ file
laz_file = download_lidar(laz_url=laz_url, data_dir=data_dir)
# Process LAZ into terrain GeoTIFFs
terrain_geotiffs = lidar_to_terrain_rasters(laz_file=laz_file, srid=srid)

# Import LAZ data into PostGIS
lidar_to_pgpointcloud(laz_file=laz_file, srid=srid)
# Import terrain rasters into PostGIS
terrain_to_postgis_rasters(terrain_geotiffs=terrain_geotiffs)

print(f'PIPELINE RUN TIME: {round(time.perf_counter() - start)} seconds')
