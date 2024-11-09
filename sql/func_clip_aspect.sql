CREATE OR REPLACE FUNCTION clip_aspect(
    aoi_geojson TEXT
)

RETURNS RASTER AS $$

DECLARE 
    aspect_rast RASTER; 

BEGIN

SELECT
    ST_Clip(
        aspect.rast,
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