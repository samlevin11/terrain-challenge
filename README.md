## 1 PostGIS Container Startup
Start the PostGIS docker container using the docker-compose file. Use the `-d` flag to run in detached mode.

`docker compose up -d`

This will start a new `postgis_terrain` container. Upon initialization the `postgis_raster` extension will be enabled.
The container uses `pgpointcloud/pointcloud` as its base image. This image comes pre-configued with the **pgPointCloud** extension enabled.

To confirm the container has started and is working as expected you may run the following command to enter the `psql` interface.

`docker exec -it postgis_terrain psql -U user -d terrain`

Confirm the activated extensions.

`\dx`

You should see the `postgis`, `postgis_raster`, `pointcloud`, and `pointcloud_postgis` extensions enabled, among others.

You may also confirm check the PostGIS version.

`SELECT POSTGIS_FULL_VERSION();`

## 2 LIDAR Processing
Scripts in the `terrain_processing` directory are used to download and process LIDAR data into a collection of terrain rasters. 

The `download_lidar.py` file is used to programmaticalyl download a LAZ file from The USGS National Map to a local data directory. 

The following script `lidar_to_terrain_rasters.py` is used to create a digital elevation model (DEM), along with slope and aspect rasters. The Whitebox Tools library is used to create these terrain rasters.

