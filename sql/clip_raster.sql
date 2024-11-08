WITH aoi AS (
    SELECT
        ST_GeomFromGeoJSON(
            '{ "type": "Polygon", "coordinates": [ [ [-105.3920602798462, 41.23480075625185], [-105.3845500946045, 41.23502666664659], [-105.38296222686768, 41.23144428127658], [-105.38866996765138, 41.2296368772165], [-105.3931760787964, 41.23170247777768], [-105.3920602798462, 41.23480075625185] ] ] }'
        ) as geom
)

, aoi_transform AS (
	SELECT ST_Transform(geom, ST_SRID(rast)) as geom
	FROM aoi, public.filleddem
)

-- SELECT  
-- 	ST_IsValid(geom), 
-- 	ST_SRID(geom),
-- 	*
-- FROM aoi

-- SELECT ST_SRID(geom), *
-- FROM aoi_transform

SELECT
	filleddem.rid id,
	ST_Clip(filleddem.rast, aoi_transform.geom) as rast
FROM aoi_transform, public.filleddem