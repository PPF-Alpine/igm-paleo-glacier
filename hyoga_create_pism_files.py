import hyoga

# UTM-32 projection, WGS 84 datum
crs = 'epsg:32632'

# west, south, east, north bounds
bounds = [150e3, 4820e3, 1050e3, 5420e3]
ds = hyoga.open.bootstrap(crs=crs, bounds=bounds, resolution=1000)
ds.to_netcdf('boot.nc')

ds = hyoga.open.atmosphere(crs=crs, bounds=bounds, resolution=1000)
ds['air_temp'] -= 6
ds.to_netcdf('atm.nc')