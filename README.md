# Quick Start

## Requirements

-   [Docker](https://docs.docker.com/engine/install/)
-   [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)

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

6. Start the Flask application
    ```bash
    python app/app.py
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

-   `data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_RawDEM.tif`
-   `data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_FilledDEM.tif`
-   `data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_Slope.tif`
-   `data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_Aspect.tif`

## 3. PostGIS Data Import

Scripts in the `postgis_data_import` directory are used to import the LIDAR data and processed terrain rasters into PostGIS.

The `lidar_to_pgpointcloud.py` script is used to import the original LAZ file into PostGIS. Using the Python API for [PDAL](https://pdal.io/en/2.6.3/about.html) is used to read the file, defining a processing pipeline in JSON. The LIDAR points are chipped into smaller chunks (chips) of approximately 400 points each. PDAL provides readers and writers compatible with the PostGIS `pgPointCloud` extension. This writer is used to import the chips to a new `pointcloud` table in the PostGIS database.

In PostGIS, the new `pointcloud` table stores this LIDAR as a table of `PcPatch` objects. Each patch represents a chip produced by PDAL, each storing a collection of approximately 400 `PcPoint` objects. While this table is not used further in this project, the `pgPointCloud` extension provides an efficient data storage model for LIDAR in PostGIS. Multiple LAS/LAZ datasets could be imported into this shared table to consolidate them into a single source.

The `terrain_to_postgis_rasters.py` script is used to import the processed terrain rasters (DEM, slope, aspect) into PostGIS. It begins by listing `.tif` (GeoTIFF) files within the `data` directory. These rasters are accessible within the container via a mounted volume.

For each GeoTIFF, its SRID is identified using [GDAL](https://gdal.org/en/latest/api/python/raster_api.html) and [OSR](https://gdal.org/en/latest/api/python/spatial_ref_api.html). Using a Python `subprocess`, the [`raster2pgsql`](https://postgis.net/docs/using_raster_dataman.html#RT_Raster_Loader) program within the PostGIS container is run. Since this program may not be available on the host machine, it can be more reliably used via the container. This converts the rasters to a SQL command that may be used to load them in PostGIS. Various flags and configurations are provided to specify the name of the new raster table (based on the filename), SRID, enforcing raster contraints, etc. Due to the relatively small size of the data, tiling is not used in this example.

Finally, the SQL output of the `raster2pgsql` command is executed via a [psycopg](https://www.psycopg.org/docs/) database connection. This creates the terrain rasters in the PostGIS DB's persistent storage volume. The following database tables are created:

-   `public.rawdem`
-   `public.filleddem`
-   `public.slope`
-   `public.aspect`

Since the `-C` option is passed when to the `raster2pgsql` program, each imported raster is properly registered in the database's [`raster_columns`](https://postgis.net/docs/using_raster_dataman.html#RT_Raster_Catalog) catalog.

## 4. PostGIS Raster Clipping[ Functions

Custom database functions are created in PostGIS to clip the terrain rasters by an Area of Interest (AOI).

These functions (`clip_dem`, `clip_slope`, and `clip_aspect`) accept a [GeoJSON](https://geojson.org/) geometry as input. The GeoJSON is converted to a PostGIS Geometry data object, which is [transformed](https://postgis.net/docs/ST_Transform.html) to match the [coordinate system](https://postgis.net/docs/RT_ST_SRID.html) of the terrain raster being clipped. Finally, the terrain raster is clipped and returned from the function as a PostGIS raster object. A fourth, final function, `clip_terrain`, calls all three clipping functions at once, consolidating how they may invoked. In this case, the clipped rasters are returned as BYTEA (byte arrays) representing GeoTIFFs, converted using the [ST_AsTIFF](https://postgis.net/docs/RT_ST_AsTIFF.html) function. For this function to work properly, [GDAL drivers](https://postgis.net/docs/postgis_gdal_enabled_drivers.html) must be enabled (configured on container startup).

The functions are stored in the `sql/func_clip_terrain.sql` file. Using a mounted volume, this directory is made available within the PostGIS Docker container. They are created in the database by connecting to the container's `psql` interface, executing the SQL file with the new functions.

## 5. Leaflet Frontend Application

A [Leaflet](https://leafletjs.com/) frontend application allows users to define an Area of Interest (AOI) to clip and view terrain data within. This application is built using vanilla JavaScript and HTML, consisting of a simple `index.html` and `main.js` file. In the future this could be enhanced to use a frontend framework like [React](https://react.dev/) or [Angular](https://angular.dev/).

As soon as the map loads, the extent of the available terrain in PostGIS is retrieved from the `/terrain_extent` endpoint and used to set the bounds of the map. A red boundary shape will display around the area of existing terrain data. This allows the application to dynamically determine where terrain exists, rather than simply initializing on a pre-defined location.

The application uses the [Leaflet-Geoman](https://geoman.io/docs/leaflet/) plugin to allow the user to define an AOI using Rectangle and Polygon drawing modes. Once and AOI has been defined, the `CLIP TERRAIN` button in the lower left corner becomes enabled. Clicking this button sends requests to the backend clipping endpoints ([explored in the following section](#6.-flask-backend-server)) based on the user's AOI. The AOI shape will be hidden once a clipping operation has been issued. Clipped terrain rasters are returned to the client as GeoTIFFs. These are loaded and displayed in the Leaflet map using the [GeoRasterLayer](https://github.com/geotiff/georaster-layer-for-leaflet) plugin.

A Leaflet layers control is used to switch between clipped terrain rasters, ensuring only one is visible in the map one once. The AOI layer may also be toggled on/off using this control. 

If desired, the user may modify their AOI shape and rerun the clipping process. The existing clipped terrain rasters will be removed from the map and replaced by the new clipped terrain rasters. To clear all clipped raster results from the map, click the `RESET RESULTS` button, which will remove the layers from the map and layer control. 


## 6. Flask Backend Server

A simple [Flask](https://flask.palletsprojects.com/en/stable/) server is used to provide access to the PostGIS database terrain data and clipping functions. The server executes queries in the PostGIS database via a `psycopg2` connection. Four endpoints are defined. 

The `/terrain_extent` endpoint is used to query the PostGIS database for the extent of the terrain rasters. Using the [ST_MinConvexHull](https://postgis.net/docs/RT_ST_MinConvexHull.html) PostGIS function, the extent of the elevation raster is retrieved. This is returned as a GeoJSON feature in WGS84 (SRID 4326). This endpoint is used to set the initial extent of the map when it loads and provide a boundary shape for the valid terrain area. 

Three endpoints are used to query the various terrain rasters: `/clip_dem`, `/clip_slope`, and `/clip_aspect`. These endpoints accept a `POST` requests containing a GeoJSON geometry in the body. This GeoJSON represents an AOI used to clip the terrain. For each endpoint, the custom clipping functions defined in the PostGIS database are invoked. 

The results are returned to the server as GeoTIFF byte arrays. Rather than returning the resulting GeoTIFF byte array to the client all at once, the results broken into many smaller chunks and streamed back to the client. This significantly improves the application performance, allowing the client to start processing and displaying the results much more rapidly. 


