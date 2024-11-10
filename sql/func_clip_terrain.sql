-- Clip filled DEM raster based on an input Area of Interest GeoJSON string
-- Results returned as a raster
CREATE OR REPLACE FUNCTION clip_dem(
    -- Accept GeoJSON text as input
    -- Defines the Area of Interest to clip terrain
    aoi_geojson TEXT
)
-- Return a PostGIS raster
RETURNS RASTER AS $$

DECLARE 
    dem_rast RASTER; 

BEGIN

SELECT
    -- Clip the Filled DEM raster based on the GeoJSON geometry
    ST_Clip(
        demfilled.rast,
        -- Project the Geometry to the same SRID as the raster before clipping
        ST_Transform(
            ST_GeomFromGeoJSON(aoi_geojson),
            ST_SRID(demfilled.rast)
        )
    ) as dem_rast 
INTO dem_rast
FROM
    public.demfilled;

RETURN dem_rast; 
   
END;
$$ LANGUAGE plpgsql;


-- Clip slope raster based on an input Area of Interest GeoJSON string
-- Results returned as a raster
CREATE OR REPLACE FUNCTION clip_slope(
    -- Accept GeoJSON text as input
    -- Defines the Area of Interest to clip terrain
    aoi_geojson TEXT
)
-- Return a PostGIS raster
RETURNS RASTER AS $$

DECLARE 
    slope_rast RASTER; 

BEGIN

SELECT
    -- Clip the slope raster based on the GeoJSON geometry
    ST_Clip(
        slope.rast,
        -- Project the Geometry to the same SRID as the raster before clipping
        ST_Transform(
            ST_GeomFromGeoJSON(aoi_geojson),
            ST_SRID(slope.rast)
        )
    ) as slope_rast 
INTO slope_rast
FROM
    public.slope;

RETURN slope_rast; 
   
END;
$$ LANGUAGE plpgsql;


-- Clip aspect raster based on an input Area of Interest GeoJSON string
-- Results returned as a raster
CREATE OR REPLACE FUNCTION clip_aspect(
    -- Accept GeoJSON text as input
    -- Defines the Area of Interest to clip terrain
    aoi_geojson TEXT
)
-- Return a PostGIS raster
RETURNS RASTER AS $$

DECLARE 
    aspect_rast RASTER; 

BEGIN

SELECT
    -- Clip the aspect raster based on the GeoJSON geometry
    ST_Clip(
        aspect.rast,
        -- Project the Geometry to the same SRID as the raster before clipping
        ST_Transform(
            ST_GeomFromGeoJSON(aoi_geojson),
            ST_SRID(aspect.rast)
        )
    ) as aspect_rast 
INTO aspect_rast
FROM
    public.aspect;

RETURN aspect_rast; 
   
END;
$$ LANGUAGE plpgsql;


-- Use prevously creatd funtions to clip all three terrain rasters at once
-- Convert results to GeoTIFF using ST_AsTIFF, as byte array
-- Results of all three clipping operations returned as a table with three columns
-- One column for each clipped raster (DEM, slope, aspect)
CREATE OR REPLACE FUNCTION clip_terrain(
    aoi_geojson TEXT
)
-- Return table with all three clipped rasters as GeoTIFFs (byte array)
RETURNS TABLE (
    dem_tiff BYTEA,
    slope_tiff BYTEA,
    aspect_tiff BYTEA
) AS $$

BEGIN
RETURN QUERY
SELECT
    -- Convert PostGIS rasters to GeoTIFF
    -- Ensure GDAL drivers are enabled 
    -- (configured in container startup, enable_extensions.sql)
    ST_AsTIFF(clip_dem(aoi_geojson)),
    ST_AsTIFF(clip_slope(aoi_geojson)),
    ST_AsTIFF(clip_aspect(aoi_geojson));
   
END;
$$ LANGUAGE plpgsql;