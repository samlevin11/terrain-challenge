import os
import time
import requests

def download_lidar(laz_url, data_dir):
    start = time.perf_counter()

    print('\n--------DOWNLOADING LIDAR DATA FROM USGS--------')

    laz_file = os.path.join(data_dir, os.path.split(laz_url)[1])
    print(f'downloading to local file: {laz_file}')

    # Use request library to retrieve and write the file to local data
    resp = requests.get(laz_url, timeout=30)
    with open(laz_file, 'wb') as file:
        file.write(resp.content)

    print(f'DOWNLOAD TIME: {round(time.perf_counter() - start)} seconds')

    return laz_file


if __name__ == '__main__':
    download_lidar(
        'https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/WY_SouthCentral_2020_D20/WY_SouthCentral_3_2020/LAZ/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640.laz',
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    )
