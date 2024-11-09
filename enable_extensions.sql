CREATE EXTENSION IF NOT EXISTS postgis_raster;
ALTER DATABASE terrain SET postgis.gdal_enabled_drivers TO 'ENABLE_ALL';