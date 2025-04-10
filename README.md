# Quick Start

## Requirements

-   [Docker](https://docs.docker.com/engine/install/)
-   [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)

## Run

1. Create an `.env` based on the `example.env` and start the PostGIS container in detached mode

    _Note: you may also simply rename `example.env` to `.env` for default environment variables_

    ```bash
    docker compose up -d
    ```

2. Create and activate Python Conda environment

    ```bash
    conda env create -f environment.yml
    conda activate terrain_env
    ```

3. Run the data pipeline to download LIDAR, process terrain raters, import LIDAR and terrain rasters into PostGIS

    _Note: the initial data download may take a couple of minutes (approximately 69MB of LIDAR data)_

    ```bash
    python terrain_pipeline.py
    ```

4. Create PostGIS functions to clip terrain rasters, substituting in the user and database name from your `.env` file

    ```bash
    docker exec -it postgis_terrain psql -U <POSTGRES_USER> -d <POSTGRES_DB> -f sql/func_clip_terrain.sql
    ```

5. Start the Flask application
    ```bash
    python app/app.py
    ```
    [Open the application on http://127.0.0.1:5000](http://127.0.0.1:5000)

# Project Description

## 1. PostGIS Container Startup

Start the PostGIS docker container using the docker-compose file. Use the `-d` flag to run in detached mode.

```bash
docker compose up -d
```

This will start a new `postgis_terrain` container. A new `terrain` database will be created. Upon initialization the `postgis_raster` extension will be enabled. The container uses `pgpointcloud/pointcloud` ([pgPointCloud](https://pgpointcloud.github.io/pointcloud/)) as its base image. This image comes pre-configured with the `pointcloud` and `pointcloud_postgis` extensions enabled.

To confirm the container has started and is woking as expected you may run the following command to enter the `psql` interface (substitute in the user and database name from your `.env` file).

```bash
docker exec -it postgis_terrain psql -U <POSTGRES_USER> -d <POSTGRES_DB>
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

## 2. Terrain Pipeline

The `terrain_pipeline.py` script is a full data pipeline for downloading LIDAR data, processing terrain rasters, and loading data into PostGIS. It invokes the scripts described below.

### 2.1. Terrain Processing

Scripts in the `terrain_processing` directory are used to download and process LIDAR data into a collection of terrain rasters (DEM, slope, and aspect).

The `download_lidar.py` script is used to programmatically download a LAZ file from The [USGS National Map](https://apps.nationalmap.gov/downloader/) to a local data directory. The python [requests](https://requests.readthedocs.io/en/latest/) library is used to retrieve the file. After downloading, the file will be saved as:

`data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640.laz`.

The following script `lidar_to_terrain_rasters.py` is used to create a digital elevation model (DEM), along with slope and aspect rasters. The [Whitebox Tools](https://www.whiteboxgeo.com/geospatial-software/) library is used to create these terrain rasters. Inverse distance weighting (IDW) interpolation is used to generate a 1 meter raw DEM. Only points classified as final ground returns (class 2, last return) are used in the interpolation. Since the initial raw DEM has NoData holes from a lack of LIDAR returns, the holes are filled to prevent data gaps. This filled DEM is then used to calculate slope (degrees) and aspect (degrees). Since this particular LAZ file does not contain coordinate reference system (CRS) information in the header, the CRS is obtained from the file [metadata](https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/metadata/WY_SouthCentral_2020_D20/WY_SouthCentral_3_2020/reports/vendor_provided_xml/WY_South_Central_3_2020_D20_Classified_Point_Cloud_Metadata_222437.xml) and determined to be NAD83 (2011) UTM Zone 13 meters (EPSG 6342). [Rasterio](https://rasterio.readthedocs.io/en/stable/intro.html) is used to assert the spatial reference of the output rasters. The following rasters are created:

-   `data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_DEMRaw.tif`
-   `data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_DEMFilled.tif`
-   `data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_Slope.tif`
-   `data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_Aspect.tif`

### 2.2. PostGIS Data Import

Scripts in the `postgis_data_import` directory are used to import the LIDAR data and processed terrain rasters into PostGIS.

The `lidar_to_pgpointcloud.py` script is used to import the original LAZ file into PostGIS. Using the Python API for [PDAL](https://pdal.io/en/2.6.3/about.html) is used to read the file, defining a processing pipeline in JSON. The LIDAR points are chipped into smaller chunks (chips) of approximately 400 points each. PDAL provides readers and writers compatible with the PostGIS `pgPointCloud` extension. This writer is used to import the chips to a new `pointcloud` table in the PostGIS database.

In PostGIS, the new `pointcloud_data` table stores this LIDAR as a table of `PcPatch` objects. Each patch represents a chip produced by PDAL, each storing a collection of approximately 400 `PcPoint` objects. While this table is not used further in this project, the `pgPointCloud` extension provides an efficient data storage model for LIDAR in PostGIS. Multiple LAS/LAZ datasets could be imported into this shared table to consolidate them into a single source.

The `terrain_to_postgis_rasters.py` script is used to import the processed terrain rasters (DEM, slope, aspect) into PostGIS. It begins by listing `.tif` (GeoTIFF) files within the `data` directory. These rasters are accessible within the container via a mounted volume.

For each GeoTIFF, its SRID is identified using [GDAL](https://gdal.org/en/latest/api/python/raster_api.html) and [OSR](https://gdal.org/en/latest/api/python/spatial_ref_api.html). Using a Python `subprocess`, the [`raster2pgsql`](https://postgis.net/docs/using_raster_dataman.html#RT_Raster_Loader) program within the PostGIS container is run. Since this program may not be available on the host machine, it can be more reliably used via the container. This converts the rasters to a SQL command that may be used to load them in PostGIS. Various flags and configurations are provided to specify the name of the new raster table (based on the filename), SRID, enforcing raster contraints, etc. Due to the relatively small size of the data, tiling is not used in this example.

Finally, the SQL output of the `raster2pgsql` command is executed via a [psycopg](https://www.psycopg.org/docs/) database connection. This creates the terrain rasters in the PostGIS DB's persistent storage volume. The following database tables are created:

-   `public.demraw`
-   `public.demfilled`
-   `public.slope`
-   `public.aspect`

Since the `-C` option is passed when to the `raster2pgsql` program, each imported raster is properly registered in the database's [`raster_columns`](https://postgis.net/docs/using_raster_dataman.html#RT_Raster_Catalog) catalog.

## 3. PostGIS Raster Clipping Functions

Custom database functions are created in PostGIS to clip the terrain rasters by an Area of Interest (AOI).

These functions (`clip_dem`, `clip_slope`, and `clip_aspect`) accept a [GeoJSON](https://geojson.org/) geometry as input. The GeoJSON is converted to a PostGIS Geometry data object, which is [transformed](https://postgis.net/docs/ST_Transform.html) to match the [coordinate system](https://postgis.net/docs/RT_ST_SRID.html) of the terrain raster being clipped. Finally, the terrain raster is clipped and returned from the function as a PostGIS raster object. A fourth, final function, `clip_terrain`, calls all three clipping functions at once, consolidating how they may invoked. In this case, the clipped rasters are returned as BYTEA (byte arrays) representing GeoTIFFs, converted using the [ST_AsTIFF](https://postgis.net/docs/RT_ST_AsTIFF.html) function. For this function to work properly, [GDAL drivers](https://postgis.net/docs/postgis_gdal_enabled_drivers.html) must be enabled (configured on container startup).

The functions are stored in the `sql/func_clip_terrain.sql` file. Using a mounted volume, this directory is made available within the PostGIS Docker container. They are created in the database by connecting to the container's `psql` interface, executing the SQL file with the new functions.

## 4. Leaflet + Flask Application

### 4.1. Leaflet Frontend Application

A [Leaflet](https://leafletjs.com/) frontend application allows users to define an Area of Interest (AOI) to clip and view terrain data within. This application is built using vanilla JavaScript and HTML, consisting of a simple `index.html` and `main.js` file. In the future this could be enhanced to use a frontend framework like [React](https://react.dev/) or [Angular](https://angular.dev/).

As soon as the map loads, the extent of the available terrain in PostGIS is retrieved from the `/terrain_extent` endpoint and used to set the bounds of the map. A red boundary shape will display around the area of existing terrain data. This allows the application to dynamically determine where terrain exists, rather than simply initializing on a pre-defined location.

The application uses the [Leaflet-Geoman](https://geoman.io/docs/leaflet/) plugin to allow the user to define an AOI using Rectangle and Polygon drawing modes. Once and AOI has been defined, the `CLIP TERRAIN` button in the lower left corner becomes enabled. Clicking this button sends requests to the backend clipping endpoints ([explored in the following section](#6-flask-backend-server)) based on the user's AOI. Clipped terrain rasters are returned to the client as GeoTIFFs. These are loaded and displayed in the Leaflet map using the [GeoRasterLayer](https://github.com/geotiff/georaster-layer-for-leaflet) plugin.

A Leaflet layers control is used to switch between clipped terrain rasters, ensuring only one is visible in the map one once. The AOI layer may also be toggled on/off using this control.

If desired, the user may modify their AOI shape and rerun the clipping process. The existing clipped terrain rasters will be removed from the map and replaced by the new clipped terrain rasters. To clear all clipped raster results from the map, click the `RESET RESULTS` button, which will remove the layers from the map and layer control.

### 4.2. Flask Backend Server

A simple [Flask](https://flask.palletsprojects.com/en/stable/) server is used to provide access to the PostGIS database terrain data and clipping functions. The server executes queries in the PostGIS database via a `psycopg2` connection. Four endpoints are defined.

The `/terrain_extent` endpoint is used to query the PostGIS database for the extent of the terrain rasters. Using the [ST_MinConvexHull](https://postgis.net/docs/RT_ST_MinConvexHull.html) PostGIS function, the extent of the elevation raster is retrieved. This is returned as a GeoJSON feature in WGS84 (SRID 4326). This endpoint is used to set the initial extent of the map when it loads and provide a boundary shape for the valid terrain area.

Three endpoints are used to query the various terrain rasters: `/clip_dem`, `/clip_slope`, and `/clip_aspect`. These endpoints accept a `POST` requests containing a GeoJSON geometry in the body. This GeoJSON represents an AOI used to clip the terrain. For each endpoint, the custom clipping functions defined in the PostGIS database are invoked.

The results are returned to the server as GeoTIFF byte arrays. Rather than returning the resulting GeoTIFF byte array to the client all at once, the results broken into many smaller chunks and streamed back to the client. This significantly improves the application performance, allowing the client to start processing and displaying the results much more rapidly.

## 5. Source Data and PostGIS Export

The .LAZ file downloaded from USGS and the processed terrain rasters are included in the `data/preprepared` directory. These data will be downloaded and created using the terrain processing scripts, but are included here for convenience.

A PostGIS database export is also included in this `data/preprepared` directory. Once all data and custom functions were added, the PostGIS database was exported using the [`pg_dump`](https://www.postgresql.org/d.ocs/current/app-pgdump.html) backup utility. The utility was run with the following parameters (variables substituted from `.env` file).

```bash
pg_dump -h <POSTGRES_HOST> -U <POSTRES_USER> -W -F c -b -v --exclude-table=public.pointcloud_data -f sql/<POSTGRES_DB>.backup <POSTGRES_DB>
```

The `-b` option includes large objects such as PostGIS rasters and pgPointCloud data in the export. The `-F c` uses the custom output format. One table, `public.pointcloud_data` was excluded due to size limitations.

# Questions and Future Improvements

**1. Imagine you are using FME Server to pull this LiDAR data over from multiple sources. Describe your methodology and the type of ETL jobs you would write to accomplish this.**

The processing methodology explored in this project could be enhanced to create a start to finish Extract, Transform, Load (ETL) pipeline.

This would begin by defining sources from which the LIDAR data should be downloaded. For most LIDAR data collections in the USGS National Map 3DEP, an inventory of available files is provided. For example, the WY_SouthCentral_2020_D20 data used in this project has a file inventory available [here](https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/WY_SouthCentral_2020_D20/WY_SouthCentral_3_2020/0_file_download_links.txt). A `cron` job could be scheduled to periodically retrieve these file inventories and compare them against inventories of previously processed data. When new files are identified, this would trigger the terrain processing pipeline. Many projects and regions could potentially be monitored for changes and new additions.

While the scripts used in this project currently process a single, pre-defined LAZ file, each new LAZ could be run through a pipeline similar to the `terrain_pipeline.py`. Scripts used here could be enhanced and refactored into more robust modules for reuse. A terrain processing module and data loading module might be appropriate to separate the two distinct stages of the pipeline. This pipeline could accepts a URL to the newly identified LAZ file. Calling this pipeline with a new file URL would kick off the process of downloading the LAZ file, processing it into terrain rasters, and loading the data into PostGIS.

Since not all LAS/LAZ files contain their spatial reference information in the header, this might need to be provided as a second argument to ensure the data is correctly defined. This can typically be retrieved from the metadata available for each file. In some cases, this spatial reference information can be identified automatically using libraries such as `laspy`.

Depending on how whether multiple projects or regions are being combined, the data might the data might need to be saved in different databases or tables to manage each area separately. Alternatively, if multiple sources are being combined, the data might need to be reprojected into a single, consistent coordinate system appropriate for the extent.

Since not all LIDAR data is collected with the same accuracy and resolution, the pipeline might also accept arguments to choose the spatial resolution of the resulting terrain rasters, IDW parameters, etc.

Ideally, this entire pipeline would be containerized in a new Docker container.

**2. How would you improve on the application you just created? What would you do to guarantee good performance of the web application for the end users?**

Since this project uses only a small sample of terrain data, optimization would be necessary to ensure its performance with national scale data.

At the database level, tiling of the terrain rasters would support more efficient querying and processing. In the current implementation, all terrain data is imported as a single terrain raster. Raster tiling would break this into many smaller tiles of uniform size. The extents of these tiles would be indexed, allowing the database to quickly identify which tiles intersect an area of interest. Then only the relevant tiles would be included in any processing or clipping operations. This would prevent unnecessary data from being loaded, a more efficient approach at the database level.

Depending on the scale of the data, [`outdb`](https://postgis.net/docs/using_raster_dataman.html#RT_Cloud_Rasters) rasters and [Cloud Optimized GeoTIFFs](http://cogeo.org/) might be used to provide more efficient data access. COGs excel at providing efficient raster data access for client applications, allowing them to request only small ranges of the data as required. Using `outdb` rasters, PostGIS can take advantage of these same range requests, allowing it to efficiently retrieve only the data necessary for a given operation. This approach would require more significant changes to the workflow established here so far, as the COGs would need to be copied to the file server and then referenced by PostGIS rather than loaded directly.

In the current Flask server implementation, clipped raster results are streamed back to the client. Depending on the size of the clipped rasters expected in production use, this chunk size might be adjusted to better balance memory usage and transfer speed.

While the current frontend application is built with vanilla JavaScript and HTML, a frontend framework such as React or Angular could be used to build a more robust UI. Using TypeScript would also offer development advantages, reducing the chance development errors with type-checking. 
