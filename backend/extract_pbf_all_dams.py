"""
One-shot PBF extractor for all dams.
Reads the India PBF file ONCE and extracts GeoJSON data for ALL dams simultaneously.
This is the fastest possible approach — O(1 pass) regardless of number of dams.

Usage:
    python backend/extract_pbf_all_dams.py
"""
import json
import math
import sys
import time
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
PROJECT    = BASE_DIR.parent
sys.path.append(str(BASE_DIR))

from app.config import SETTLEMENTS_DIR, RIVERS_DIR, DAMS_DIR

PBF_PATH = next(PROJECT.glob("*.osm.pbf"), None)

# ── OSM Tag filters ──────────────────────────────────────────────────────────
PLACE_TYPES    = {"city", "town", "village", "hamlet"}
AMENITY_TYPES  = {"hospital", "school", "fire_station"}
HIGHWAY_TYPES  = {"motorway", "trunk", "primary", "secondary"}
WATERWAY_TYPES = {"river", "canal"}
POP_DEFAULTS   = {"city": 100000, "town": 25000, "village": 5000, "hamlet": 500}


def bbox_for_dam(lat, lon, radius_km):
    delta_lat = radius_km / 111.32
    delta_lon = radius_km / (111.32 * math.cos(math.radians(lat)))
    return (lat - delta_lat, lon - delta_lon, lat + delta_lat, lon + delta_lon)


def extract_all(dams, radius_km=120.0):
    """
    Single-pass extraction: reads the PBF once and populates data for all dams.
    Returns: dict of dam_id -> {settlements, roads, rivers}
    """
    import osmium

    if not PBF_PATH or not PBF_PATH.exists():
        print(f"[ERROR] PBF file not found in {PROJECT}")
        sys.exit(1)

    print(f"[PBF Extractor] File: {PBF_PATH.name} ({PBF_PATH.stat().st_size // (1024*1024)} MB)")
    print(f"[PBF Extractor] Processing {len(dams)} dams in a single pass...")

    # Pre-compute bounding boxes for each dam
    dam_bboxes = {}
    for dam in dams:
        dam_id = dam["id"]
        lat, lon = dam["lat"], dam["lon"]
        dam_bboxes[dam_id] = {
            "bbox": bbox_for_dam(lat, lon, radius_km),
            "settlements": [],
            "roads": [],
            "rivers": [],
            "seen_ids": set(),
        }

    t0 = time.time()
    nodes_processed = 0
    ways_processed = 0

    fp = osmium.FileProcessor(str(PBF_PATH)).with_locations()

    for obj in fp:
        tags = {kv.k: kv.v for kv in obj.tags}

        # ── NODE: settlements & amenities ────────────────────────────────────
        if isinstance(obj, osmium.osm.Node):
            place   = tags.get("place")
            amenity = tags.get("amenity")
            if place not in PLACE_TYPES and amenity not in AMENITY_TYPES:
                continue

            try:
                nlat, nlon = obj.location.lat, obj.location.lon
            except Exception:
                continue

            nodes_processed += 1
            name       = tags.get("name", tags.get("name:en", "Unknown"))
            place_type = place or amenity or "settlement"
            pop = 0
            if "population" in tags:
                try:    pop = int(tags["population"])
                except: pass
            else:
                pop = POP_DEFAULTS.get(place_type, 0)

            feature = {
                "type": "Feature",
                "properties": {
                    "name": name, "type": place_type,
                    "population": pop, "elevation_m": 0,
                    "source": "OpenStreetMap"
                },
                "geometry": {"type": "Point", "coordinates": [nlon, nlat]}
            }

            # Add to every dam whose bbox contains this node
            for dam_id, d in dam_bboxes.items():
                s, w, n, e = d["bbox"]
                if s <= nlat <= n and w <= nlon <= e:
                    if obj.id not in d["seen_ids"]:
                        d["seen_ids"].add(obj.id)
                        d["settlements"].append(feature)

        # ── WAY: roads & rivers ──────────────────────────────────────────────
        elif isinstance(obj, osmium.osm.Way):
            highway  = tags.get("highway")
            waterway = tags.get("waterway")
            if highway not in HIGHWAY_TYPES and waterway not in WATERWAY_TYPES:
                continue

            coords = []
            for node in obj.nodes:
                try:
                    if node.location.valid():
                        coords.append([node.location.lon, node.location.lat])
                except Exception:
                    continue

            if len(coords) < 2:
                continue

            ways_processed += 1

            if highway in HIGHWAY_TYPES:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "name": tags.get("name", tags.get("ref", "Road")),
                        "category": highway,
                        "source": "OpenStreetMap"
                    },
                    "geometry": {"type": "LineString", "coordinates": coords}
                }
                key = "roads"
            else:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "name": tags.get("name", "River"),
                        "waterway": waterway,
                        "source": "OpenStreetMap"
                    },
                    "geometry": {"type": "LineString", "coordinates": coords}
                }
                key = "rivers"

            # Check which dams contain any node of this way
            for dam_id, d in dam_bboxes.items():
                if obj.id in d["seen_ids"]:
                    continue
                s, w, n, e = d["bbox"]
                in_bbox = any(s <= c[1] <= n and w <= c[0] <= e for c in coords)
                if in_bbox:
                    d["seen_ids"].add(obj.id)
                    d[key].append(feature)

    elapsed = time.time() - t0
    print(f"[PBF Extractor] Scan complete in {elapsed:.1f}s — "
          f"{nodes_processed} settlement nodes, {ways_processed} road/river ways processed.")

    return dam_bboxes


def save_results(dam_bboxes):
    """Save extracted GeoJSON files to cache directories."""
    saved = 0
    skipped = 0
    for dam_id, d in dam_bboxes.items():
        settlements_file = SETTLEMENTS_DIR / f"{dam_id}_settlements.geojson"
        roads_file       = SETTLEMENTS_DIR / f"{dam_id}_roads.geojson"
        river_file       = RIVERS_DIR      / f"{dam_id}_river.geojson"

        # Don't overwrite existing valid files
        if settlements_file.exists() and roads_file.exists() and river_file.exists():
            skipped += 1
            continue

        s_fc = {"type": "FeatureCollection", "features": d["settlements"]}
        r_fc = {"type": "FeatureCollection", "features": d["roads"]}
        ri_fc = {"type": "FeatureCollection", "features": d["rivers"]}

        settlements_file.write_text(json.dumps(s_fc, indent=2))
        roads_file.write_text(json.dumps(r_fc, indent=2))
        river_file.write_text(json.dumps(ri_fc, indent=2))

        print(f"  [{dam_id}] Saved: {len(d['settlements'])} settlements, "
              f"{len(d['roads'])} roads, {len(d['rivers'])} rivers.")
        saved += 1

    print(f"\n[PBF Extractor] Done! Saved: {saved} dams, Skipped (already cached): {skipped} dams.")


def main():
    dams_file = DAMS_DIR / "dams.json"
    if not dams_file.exists():
        print(f"[ERROR] dams.json not found at {dams_file}")
        sys.exit(1)

    dams = json.loads(dams_file.read_text())

    # Only process dams that don't already have all 3 cache files
    pending = [
        d for d in dams
        if not (
            (RIVERS_DIR / f"{d['id']}_river.geojson").exists() and
            (SETTLEMENTS_DIR / f"{d['id']}_settlements.geojson").exists() and
            (SETTLEMENTS_DIR / f"{d['id']}_roads.geojson").exists()
        )
    ]

    if not pending:
        print("[PBF Extractor] All dams already have cached OSM data! Nothing to do.")
        return

    print(f"[PBF Extractor] {len(pending)} dams need OSM data (out of {len(dams)} total).")
    dam_bboxes = extract_all(pending, radius_km=120.0)
    save_results(dam_bboxes)


if __name__ == "__main__":
    main()
