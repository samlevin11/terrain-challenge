# Quick Start

## Requirements
- [Docker](https://docs.docker.com/engine/install/)
- [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
- [Node](https://nodejs.org/en/learn/getting-started/how-to-install-nodejs)

## Run
1. Start the PostGIS container

    ```bash 
    docker compose up -d
    ```

2. Create Python Conda environment
    ```bash 
    conda env create -f environment.yml
    conda activate terrain_env
    ```

3. Download LIDAR data and process terrain
    ```bash 
    python terrain_processing/download_lidar.py
    python terrain_processing/lidar_to_terrain_rasters.py
    ```

4. Import LIDAR data and terrain rasters into PostGIS
    ```bash
    python postgis_data_import/lidar_to_pgpointcloud.py
    python postgis_data_import/terrain_to_postgis_rasters.py
    ```

5. Create PostGIS functions to clip terrain rasters
    ```bash
    docker exec -it postgis_terrain psql -U user -d terrain -f sql/func_clip_terrain.sql
    ```

# Project Description

## 1. PostGIS Container Startup
Start the PostGIS docker container using the docker-compose file. Use the `-d` flag to run in detached mode.

```bash
docker compose up -d
```

This will start a new `postgis_terrain` container. A new `terrain` database will be created. Upon initialization the `postgis_raster` extension will be enabled. The container uses `pgpointcloud/pointcloud` (**[pgPointCloud](https://pgpointcloud.github.io/pointcloud/)**) as its base image. This image comes pre-configured with the `pointcloud` and `pointcloud_postgis` extensions enabled.

To confirm the container has started and is woking as expected you may run the following command to enter the `psql` interface.

```bash
docker exec -it postgis_terrain psql -U user -d terrain
```

In the `psql` terminal, confirm the activated extensions.

```sql 
\dx
```

You should see the `postgis`, `postgis_raster`, `pointcloud`, and `pointcloud_postgis` extensions enabled, among others.

You may also confirm the PostGIS version (3.4).

```sql
SELECT POSTGIS_FULL_VERSION();
```

Four volumes are mounted to the container.

1. A volume to provide persistent PostGIS data storage
2. A volume to provide startup SQL scripts for PostGIS
3. A volume to make terrain data available within the `postgis_terrain` container
4. A volume to make new SQL functions available within the `postgis_terrain` container 

An initialization script mounted to `docker-entrypoint-initdb.d` is used to enable the `postgis_raster` extension and [enable GDAL drivers](https://postgis.net/docs/postgis_gdal_enabled_drivers.html) on startup.

## 2. LIDAR Processing
Scripts in the `terrain_processing` directory are used to download and process LIDAR data into a collection of terrain rasters (DEM, slope, and aspect). 

The `download_lidar.py` script is used to programmatically download a LAZ file from The [USGS National Map](https://apps.nationalmap.gov/downloader/) to a local data directory. The python [requests](https://requests.readthedocs.io/en/latest/) library is used to retrieve the file. After downloading, the file will be saved as:

`data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640.laz`.

The following script `lidar_to_terrain_rasters.py` is used to create a digital elevation model (DEM), along with slope and aspect rasters. The [Whitebox Tools](https://www.whiteboxgeo.com/geospatial-software/) library is used to create these terrain rasters. Inverse distance weighting (IDW) interpolation is used to generate a 1 meter raw DEM. Only points classified as final ground returns (class 2, last return) are used in the interpolation. Since the initial raw DEM has NoData holes from a lack of LIDAR returns, the holes are filled to prevent data gaps. This filled DEM is then used to calculate slope (degrees) and aspect (degrees). Since this particular LAZ file does not contain coordinate reference system (CRS) information in the header, the CRS is obtained from the file [metadata](https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/metadata/WY_SouthCentral_2020_D20/WY_SouthCentral_3_2020/reports/vendor_provided_xml/WY_South_Central_3_2020_D20_Classified_Point_Cloud_Metadata_222437.xml) and determined to be NAD83 (2011) UTM Zone 13 meters (EPSG 6342). [Rasterio](https://rasterio.readthedocs.io/en/stable/intro.html) is used to assert the spatial reference of the output rasters. The following rasters are created:

`data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_RawDEM.tif`
`data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_FilledDEM.tif`
`data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_Slope.tif`
`data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_Aspect.tif`

## 3. PostGIS Data Import

Scripts in the `postgis_data_import` directory are used to import the LIDAR data and processed terrain rasters into PostGIS.

The `lidar_to_pgpointcloud.py` script is used to import the original LAZ file into PostGIS. Using the Python API for [PDAL](https://pdal.io/en/2.6.3/about.html) is used to read the file, defining a processing pipeline in JSON. The LIDAR points are chipped into smaller chunks (chips) of approximately 400 points each. PDAL provides readers and writers compatible with the PostGIS `pgPointCloud` extension. This writer is used to import the chips to a new `pointcloud` table in the PostGIS database.

In PostGIS, the new `pointcloud` table stores this LIDAR as a table of `PcPatch` objects. Each patch represents a chip produced by PDAL, each storing a collection of approximately 400 `PcPoint` objects. While this table is not used further in this project, the `pgPointCloud` extension provides an efficient data storage model for LIDAR in PostGIS. Multiple LAS/LAZ datasets could be imported into this shared table to consolidate them into a single source.

The `terrain_to_postgis_rasters.py` script is used to import the processed terrain rasters (DEM, slope, aspect) into PostGIS. It begins by listing `.tif` (GeoTIFF) files within the `data` directory. These rasters are accessible within the container via a mounted volume.

For each GeoTIFF, its SRID is identified using [GDAL](https://gdal.org/en/latest/api/python/raster_api.html) and [OSR](https://gdal.org/en/latest/api/python/spatial_ref_api.html).  Using a Python `subprocess`, the [`raster2pgsql`](https://postgis.net/docs/using_raster_dataman.html#RT_Raster_Loader) program within the PostGIS container is run. Since this program may not be available on the host machine, it can be more reliably used via the container. This converts the rasters to a SQL command that may be used to load them in PostGIS. Various flags and configurations are provided to specify the name of the new raster table (based on the filename), SRID, enforcing raster contraints, etc. Due to the relatively small size of the data, tiling is not used in this example. 

Finally, the SQL output of the `raster2pgsql` command is executed via a [psycopg](https://www.psycopg.org/docs/) database connection. This creates the terrain rasters in the PostGIS DB's persistent storage volume.

## 4 PostGIS Raster Clipping Functions
