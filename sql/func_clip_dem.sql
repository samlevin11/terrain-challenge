CREATE OR REPLACE FUNCTION clip_dem(
    aoi_geojson TEXT
)

RETURNS RASTER AS $$

DECLARE 
    dem_rast RASTER; 

BEGIN

SELECT
    ST_Clip(
        filleddem.rast,
        ST_Transform(
            ST_GeomFromGeoJSON(aoi_geojson),
            ST_SRID(filleddem.rast)
        )
    ) as dem_rast 
INTO dem_rast
FROM
    public.filleddem;

RETURN dem_rast; 
   
END;
$$ LANGUAGE plpgsql;