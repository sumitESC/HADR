import json
from pathlib import Path
from shapely.geometry import shape, Point, LineString
from app.config import SETTLEMENTS_DIR


class ExposureAnalyzer:
    def __init__(self):
        """
        Exposure analyzer. Data is loaded per-dam via load_dynamic_data()
        which is called by SimulationManager with the correct dam-specific files.
        """
        self.settlements = []
        self.roads = []

    def load_dynamic_data(self, settlements_geojson: dict, roads_geojson: dict):
        """Load settlements and roads from dynamically fetched OSM data."""
        self.settlements = settlements_geojson.get("features", [])
        self.roads = roads_geojson.get("features", [])

    def analyze_exposure(self, flood_geojson: dict):
        """
        Intersects flood extent polygon with settlements and road features.
        Returns exposure summary metrics.
        """
        flood_features = flood_geojson.get("features", [])
        if not flood_features:
            return {
                "settlements_flooded_count": 0,
                "total_population_exposed": 0,
                "affected_settlements": [],
                "flooded_roads_km": 0.0,
                "affected_roads": [],
                "bridges_at_risk": 0,
                "hospitals_at_risk": 0,
                "schools_at_risk": 0
            }
            
        # Merge flood geometries
        flood_geoms = []
        for f in flood_features:
            try:
                geom = shape(f.get("geometry", {}))
                if geom.is_valid and not geom.is_empty:
                    flood_geoms.append(geom)
            except Exception:
                continue
        
        if not flood_geoms:
            return {
                "settlements_flooded_count": 0,
                "total_population_exposed": 0,
                "affected_settlements": [],
                "flooded_roads_km": 0.0,
                "affected_roads": [],
                "bridges_at_risk": 0,
                "hospitals_at_risk": 0,
                "schools_at_risk": 0
            }

        affected_settlements = []
        total_pop = 0
        hospitals = 0
        schools = 0
        total_estimated_loss_inr = 0.0

        for feat in self.settlements:
            props = feat.get("properties", {})
            try:
                geom = shape(feat["geometry"])
            except Exception:
                continue

            # Find maximum water depth intersecting this settlement
            max_depth_m = 0.0
            for f in flood_features:
                try:
                    fg = shape(f.get("geometry", {}))
                    if fg.intersects(geom):
                        min_d = f.get("properties", {}).get("min_depth", 0.1)
                        if min_d > max_depth_m:
                            max_depth_m = min_d
                except Exception:
                    continue

            if max_depth_m > 0:
                pop = props.get("population", 0)
                total_pop += pop
                place_type = props.get("type", "settlement")

                if place_type == "hospital":
                    hospitals += 1
                elif place_type == "school":
                    schools += 1

                # Depth-damage curve function D(h)
                if max_depth_m >= 4.0:
                    damage_pct = 95
                    hazard_label = "Catastrophic (Total Destruction)"
                    evac_status = "Mandatory Evacuation"
                elif max_depth_m >= 3.0:
                    damage_pct = 80
                    hazard_label = "Severe (Major Structural Loss)"
                    evac_status = "Mandatory Evacuation"
                elif max_depth_m >= 2.0:
                    damage_pct = 60
                    hazard_label = "High (Building Inundated)"
                    evac_status = "Evacuation Advised"
                elif max_depth_m >= 1.0:
                    damage_pct = 35
                    hazard_label = "Moderate (Ground Floor Flooded)"
                    evac_status = "High Alert"
                elif max_depth_m >= 0.5:
                    damage_pct = 15
                    hazard_label = "Low (Water Ingress)"
                    evac_status = "Watch / Warning"
                else:
                    damage_pct = 5
                    hazard_label = "Minor Logging"
                    evac_status = "Monitored"

                # Financial structural loss estimation (₹)
                est_loss = round(pop * (damage_pct / 100.0) * 150000.0, 2)
                total_estimated_loss_inr += est_loss

                affected_settlements.append({
                    "name": props.get("name", "Unknown"),
                    "type": place_type,
                    "population": pop,
                    "water_depth_m": max_depth_m,
                    "damage_ratio_pct": damage_pct,
                    "hazard_level": hazard_label,
                    "evacuation_status": evac_status,
                    "estimated_loss_inr": est_loss,
                    "elevation_m": props.get("elevation_m", 0),
                    "coordinates": feat["geometry"].get("coordinates", [0, 0])
                })

        affected_roads = []
        total_road_km = 0.0

        for feat in self.roads:
            props = feat.get("properties", {})
            try:
                road_geom = shape(feat["geometry"])
            except Exception:
                continue

            intersected_length_deg = 0.0
            max_road_depth = 0.0
            for f in flood_features:
                try:
                    fg = shape(f.get("geometry", {}))
                    if fg.intersects(road_geom):
                        intersection = fg.intersection(road_geom)
                        intersected_length_deg += intersection.length
                        min_d = f.get("properties", {}).get("min_depth", 0.1)
                        if min_d > max_road_depth:
                            max_road_depth = min_d
                except Exception:
                    continue

            # 1 deg lat/lon ~ 100 km approximation
            flooded_km = round(intersected_length_deg * 100.0, 2)
            if flooded_km > 0:
                total_road_km += flooded_km
                affected_roads.append({
                    "name": props.get("name", "Road segment"),
                    "category": props.get("category", "highway"),
                    "flooded_length_km": flooded_km,
                    "max_water_depth_m": max_road_depth,
                    "traffic_status": "Impassable / Closed" if max_road_depth >= 0.5 else "Drive with Caution"
                })

        # Count actual bridges based on properties or name
        real_bridges_count = 0
        for road in affected_roads:
            name = road["name"].lower()
            if "bridge" in name or "setu" in name or "pul" in name:
                real_bridges_count += 1

        return {
            "settlements_flooded_count": len(affected_settlements),
            "total_population_exposed": total_pop,
            "affected_settlements": affected_settlements,
            "flooded_roads_km": round(total_road_km, 2),
            "affected_roads": affected_roads,
            "bridges_at_risk": real_bridges_count,
            "hospitals_at_risk": hospitals,
            "schools_at_risk": schools,
            "total_estimated_damage_inr_cr": round(total_estimated_loss_inr / 10000000.0, 2)
        }
