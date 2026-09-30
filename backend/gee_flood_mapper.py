import ee
import os

def authenticate_and_initialize():
    try:
        ee.Initialize()
    except Exception as e:
        print("Earth Engine not initialized. Authenticating...")
        ee.Authenticate()
        ee.Initialize()

def otsu_threshold(histogram):
    """
    Computes Otsu's optimal threshold from an EE histogram.
    """
    counts = ee.Array(ee.Dictionary(histogram).get('histogram'))
    means = ee.Array(ee.Dictionary(histogram).get('bucketMeans'))
    size = means.length().get([0])
    total = counts.reduce(ee.Reducer.sum(), [0]).get([0])
    sumB = ee.Number(0)
    wB = ee.Number(0)
    maximum = ee.Number(0)
    sum1 = counts.multiply(means).reduce(ee.Reducer.sum(), [0]).get([0])
    level = ee.Number(0)
    
    indices = ee.List.sequence(0, size.subtract(1))
    
    def compute_bcv(i, prev):
        prev_dict = ee.Dictionary(prev)
        wB = ee.Number(prev_dict.get('wB')).add(counts.get([i]))
        wF = total.subtract(wB)
        
        sumB_new = ee.Number(prev_dict.get('sumB')).add(counts.get([i]).multiply(means.get([i])))
        mB = sumB_new.divide(wB)
        mF = sum1.subtract(sumB_new).divide(wF)
        
        betweenClassVariance = wB.multiply(wF).multiply(mB.subtract(mF).pow(2))
        
        max_val = ee.Number(prev_dict.get('maximum'))
        lvl = ee.Number(prev_dict.get('level'))
        
        cond = betweenClassVariance.gt(max_val)
        new_max = ee.Algorithms.If(cond, betweenClassVariance, max_val)
        new_lvl = ee.Algorithms.If(cond, means.get([i]), lvl)
        
        return ee.Dictionary({
            'wB': wB,
            'sumB': sumB_new,
            'maximum': new_max,
            'level': new_lvl
        })

    initial = ee.Dictionary({'wB': 0, 'sumB': 0, 'maximum': 0, 'level': 0})
    result = ee.Dictionary(indices.iterate(compute_bcv, initial))
    return result.get('level')

def export_flood_map(region_of_interest, start_date, end_date, output_path):
    """
    Advanced Sentinel-1 SAR flood mapping:
    - Bimodal Otsu Thresholding
    - Topographic Shadow Masking (Slope)
    - JRC Permanent Water Masking
    """
    authenticate_and_initialize()

    # 1. Fetch & Filter Sentinel-1
    collection = ee.ImageCollection('COPERNICUS/S1_GRD') \
        .filterBounds(region_of_interest) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
        .filter(ee.Filter.eq('instrumentMode', 'IW'))

    list_images = collection.toList(collection.size())
    mid_index = collection.size().divide(2).int()
    
    pre_flood = ee.ImageCollection(list_images.slice(0, mid_index)).median()
    post_flood = ee.ImageCollection(list_images.slice(mid_index)).median()

    # 2. Advanced Speckle Filtering (Refined Lee / Focal Median)
    SMOOTHING_RADIUS = 50
    pre_flood_filtered = pre_flood.focal_median(SMOOTHING_RADIUS, 'circle', 'meters')
    post_flood_filtered = post_flood.focal_median(SMOOTHING_RADIUS, 'circle', 'meters')

    # Difference in dB
    difference = pre_flood_filtered.subtract(post_flood_filtered)

    # 3. Dynamic Otsu Thresholding
    histogram = difference.select('VV').reduceRegion(
        reducer=ee.Reducer.histogram(255, 2)
            .combine('mean', None, True)
            .combine('variance', None, True), 
        geometry=region_of_interest, 
        scale=30,
        maxPixels=1e10
    )
    # Fallback to 1.25 threshold if Otsu fails
    otsu_level = ee.Algorithms.If(
        ee.Dictionary(histogram).contains('VV_histogram'),
        otsu_threshold(histogram.get('VV_histogram')),
        1.25
    )
    
    # Extract Flood mask
    flood_mask = difference.gt(ee.Image.constant(otsu_level))

    # 4. Topographic Masking (Radar Shadows create false positives in valleys)
    dem = ee.Image("COPERNICUS/DEM/GLO30")
    slope = ee.Terrain.slope(dem)
    # Mask out areas with > 5 degrees slope (unlikely to pool water)
    flat_terrain_mask = slope.lt(5)

    # 5. Permanent Water Masking
    gsw = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
    permanent_water = gsw.select('transition').eq(1)
    
    # Combine masks
    final_flood_extent = flood_mask \
        .updateMask(permanent_water.unmask().Not()) \
        .updateMask(flat_terrain_mask)

    print(f"Exporting Advanced Flood Map. Calculated Otsu Threshold: {otsu_level.getInfo()} dB Drop")
    
    # Generate multi-band output for analysis
    output_image = ee.Image.cat([
        post_flood_filtered.rename('post_flood_vv'),
        difference.rename('backscatter_drop'),
        final_flood_extent.rename('flood_mask')
    ])

    task = ee.batch.Export.image.toDrive(
        image=output_image,
        description='Sentinel1_Advanced_Flood_Extent',
        folder='SIH_Outputs',
        fileNamePrefix='flood_extent_sar_advanced',
        region=region_of_interest,
        scale=30,
        crs='EPSG:4326',
        maxPixels=1e10
    )
    task.start()
    print("Advanced GEE Export task started. Check Google Drive.")

if __name__ == "__main__":
    uttarakhand_roi = ee.Geometry.Polygon(
        [[[79.6, 30.4],
          [79.8, 30.4],
          [79.8, 30.6],
          [79.6, 30.6],
          [79.6, 30.4]]]
    )
    
    export_flood_map(
        region_of_interest=uttarakhand_roi,
        start_date='2021-01-15',
        end_date='2021-02-28',
        output_path='flood_extent_sar.tif'
    )
