import shapefile

r = shapefile.Reader("departements-20180101-shp/departements-20180101.shp")

for field in r.fields:
    print(field)
