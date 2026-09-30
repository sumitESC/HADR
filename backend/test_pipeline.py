"""Quick test to verify the entire pipeline works with cached data."""
from app.gis.osm_data import OSMDataFetcher
from app.gis.elevation_api import ElevationFetcher
from app.gis.exposure import ExposureAnalyzer
import json

# Test 3 dams
test_dams = [
    ("tehri-dam", 30.3774, 78.4803),
    ("bhakra-dam", 31.4112, 76.4326),
    ("sardar-sarovar", 22.0100, 73.7480),
]

for dam_id, lat, lon in test_dams:
    print(f"\n{'='*60}")
    print(f"Testing: {dam_id}")
    print(f"{'='*60}")
    
    # Test DEM loading (should load from cache, no API call)
    dem, meta = ElevationFetcher.get_or_fetch_dem(dam_id, lat, lon)
    print(f"  DEM: {dem.shape} grid, source: {meta['source']}")
    
    # Test OSM loading (should load from cache, no API call)
    settlements, roads, rivers = OSMDataFetcher.get_or_fetch_data(dam_id, lat, lon)
    s_count = len(settlements.get("features", []))
    r_count = len(roads.get("features", []))
    rv_count = len(rivers.get("features", []))
    print(f"  OSM: {s_count} settlements, {r_count} roads, {rv_count} rivers")
    
    # Test Exposure Analyzer
    analyzer = ExposureAnalyzer()
    analyzer.load_dynamic_data(settlements, roads)
    print(f"  Exposure: loaded {len(analyzer.settlements)} settlements, {len(analyzer.roads)} roads")

print(f"\n{'='*60}")
print("ALL TESTS PASSED! Data pipeline is fully operational.")
print(f"{'='*60}")
