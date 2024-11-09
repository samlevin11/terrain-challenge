CREATE OR REPLACE FUNCTION clip_slope(
    aoi_geojson TEXT
)

RETURNS RASTER AS $$

DECLARE 
    slope_rast RASTER; 

BEGIN

SELECT
    ST_Clip(
        slope.rast,
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