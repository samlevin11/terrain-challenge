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
    ```

# Project Description

## 1. PostGIS Container Startup
Start the PostGIS docker container using the docker-compose file. Use the `-d` flag to run in detached mode.

```bash
docker compose up -d
```

This will start a new `postgis_terrain` container. Upon initialization the `postgis_raster` extension will be enabled.
The container uses `pgpointcloud/pointcloud` (**[pgPointCloud](https://pgpointcloud.github.io/pointcloud/)**) as its base image. This image comes pre-configured with the `pointcloud` and `pointcloud_postgis` extensions enabled.

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

## 2. LIDAR Processing
Scripts in the `terrain_processing` directory are used to download and process LIDAR data into a collection of terrain rasters (DEM, slope, and aspect). 

The `download_lidar.py` file is used to programmatically download a LAZ file from The [USGS National Map](https://apps.nationalmap.gov/downloader/) to a local data directory. The python [requests](https://requests.readthedocs.io/en/latest/) library is used to retrieve the file. After downloading, the file will be saved as:

`data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640.laz`.

The following script `lidar_to_terrain_rasters.py` is used to create a digital elevation model (DEM), along with slope and aspect rasters. The [Whitebox Tools](https://www.whiteboxgeo.com/geospatial-software/) library is used to create these terrain rasters. Inverse distance weighting (IDW) interpolation is used to generate a 1 meter raw DEM. Only points classified as final ground returns (class 2, last return) are used in the interpolation. Since the initial raw DEM has NoData holes from a lack of LIDAR returns, the holes are filled to prevent data gaps. This filled DEM is then used to calculate slope (degrees) and aspect (degrees). [Rasterio](https://rasterio.readthedocs.io/en/stable/intro.html) is used to assert the spatial reference of the output rasters. The following rasters are created:

`data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_RawDEM.tif`
`data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_FilledDEM.tif`
`data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_Slope.tif`
`data/USGS_LPC_WY_SouthCentral_2020_D20_13TDF670640_Aspect.tif`

