import os
import time
import whitebox
import rasterio
from rasterio.crs import CRS

def lidar_to_terrain_rasters(laz_file, srid):
    start = time.perf_counter()

    print('\n--------PROCESSING LIDAR INTO TERRAIN RASTERS--------')
    # Set data directory where LAZ was previously downloaded
    data_dir = os.path.split(laz_file)[0]

    # Intialize Whitebox Tools
    wbt = whitebox.WhiteboxTools()
    print(f'setting WBT working directory: {data_dir}')
    wbt.set_working_dir(data_dir)

    # Use IDW interpolation to create a raw DEM from the LAZ
    # Only include LAST returns, class 2 points (ground)
    # 1 meter resolution
    print('interpolating raw DEM LAZ')
    raw_dem = os.path.splitext(laz_file)[0] + '_DEMRaw.tif'
    wbt.lidar_idw_interpolation(
        i=laz_file,
        output=raw_dem,
        parameter="elevation",
        returns="last",
        exclude_cls='0,1,3-18',
        resolution=1.0,
        weight=1.0,
        radius=2.5
    )
    print(raw_dem)

    print('defining DEM coordinate reference system')
    # CRS specified in product metadata
    # Not defined LAZ header
    crs = CRS.from_epsg(srid)
    with rasterio.open(os.path.join(data_dir, raw_dem), 'r+') as dem:
        dem.crs = crs

    print('filling nodata holes')
    # Fill NoData holes in the DEM
    filled_dem = os.path.splitext(laz_file)[0] + '_DEMFilled.tif'
    wbt.fill_missing_data(
        i=raw_dem,
        output=filled_dem,
        filter=20
    )
    print(filled_dem)

    print('calculating slope')
    # Calculate Slope using filled DEM
    slope_rast = os.path.splitext(laz_file)[0] + '_Slope.tif'
    wbt.slope(
        dem=filled_dem,
        output=slope_rast,
        units='degrees'
    )
    print(slope_rast)

    print('calculating aspect')
    # Calculate Aspect using filled DEM
    aspect_rast = os.path.splitext(laz_file)[0] + '_Aspect.tif'
    wbt.aspect(
        dem=filled_dem,
        output=aspect_rast
    )
    print(aspect_rast)

    print(f'TERRAIN PROCESSING TIME: {round(time.perf_counter() - start)} seconds')

    terrain_rasters = [raw_dem, filled_dem, slope_rast, aspect_rast]

    # Print final terrain raster paths
    for tr in terrain_rasters:
        print('\t' + tr)

    return terrain_rasters


if __name__ == '__main__':
    lidar_to_terrain_rasters(
        os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data')),
            'USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640.laz'
        ),
        6342
    )
