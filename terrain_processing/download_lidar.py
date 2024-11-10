import os
import time
import requests

start = time.perf_counter()

print('\n--------DOWNLOADING LIDAR DATA FROM USGS--------')

# Define the shared volume directory to download the LAZ file to
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))

# Metadata links
# https://www.sciencebase.gov/catalog/item/62b6b4a2d34e8f4977cc320a
# https://prd-tnm.s3.amazonaws.com/index.html?prefix=StagedProducts/Elevation/metadata/WY_SouthCentral_2020_D20/WY_SouthCentral_3_2020
laz_url = 'https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/WY_SouthCentral_2020_D20/WY_SouthCentral_3_2020/LAZ/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640.laz'

laz_path = os.path.join(data_dir, os.path.split(laz_url)[1])
print(f'downloading to local file: {laz_path}')

# Use request library to retrieve and write the file to local data
resp = requests.get(laz_url, timeout=10)
with open(laz_path, 'wb') as file:
    file.write(resp.content)

print(f'DOWNLOAD TIME: {round(time.perf_counter() - start)} seconds')
