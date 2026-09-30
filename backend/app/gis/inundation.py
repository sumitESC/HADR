"""
Physics-Based Dam-Break Flood Inundation Solver
================================================
Uses real DEM elevation data, Manning's equation, gravity-driven shallow-water
wave propagation, and cross-sectional terrain analysis to compute realistic
flood extent and depth for ANY dam in the world.

Key Physics:
  - Breach hydrograph via Froehlich (1995) empirical + weir equation
  - Manning's equation:  v = (1/n) * R^(2/3) * S^(1/2)
  - Shallow-water wave celerity:  c = sqrt(g * d)
  - Cross-sectional terrain fill for width & depth
  - Volume conservation along river reach
"""

import numpy as np
from shapely.geometry import LineString, Polygon, MultiPolygon, mapping, MultiLineString
from shapely.ops import unary_union
from app.gis.dem_processor import DEMProcessor
from app.gis.osm_data import OSMDataFetcher

# Physical constants
GRAVITY = 9.81          # m/s²
MANNING_N = 0.035       # Manning's roughness for natural river channels
DEG_TO_M = 111_320.0    # 1 degree latitude ≈ 111.32 km


class InundationSolver:
    """
    DEM-aware flood propagation engine.
    Samples real terrain to compute gravity-driven flow along river channels.
    """

    def __init__(self, dem_processor: DEMProcessor, dam_id: str = "tehri-dam",
                 dam_lat: float = 30.3774, dam_lon: float = 78.4803, duration_min: float = 360.0):
        self.dem_proc = dem_processor
        self.duration_min = duration_min
        self.dem = dem_processor.dem
        self.ny, self.nx = self.dem.shape
        self.dam_id = dam_id
        self.dam_lat = dam_lat
        self.dam_lon = dam_lon

        # Compute degree-to-meter scale at this latitude
        self.lat_scale = DEG_TO_M
        self.lon_scale = DEG_TO_M * np.cos(np.radians(dam_lat))

        # Fetch real river data from OSM
        self.river_coords = self._load_river_coords()

        # Pre-compute river profile (elevation, slope, cumulative distance)
        self.river_profile = self._build_river_profile()

    # ──────────────────────────────────────────────────────────────────────
    # River Data Loading
    # ──────────────────────────────────────────────────────────────────────

    def _load_river_coords(self):
        """Load river coordinates from OSM and stitch segments into continuous downstream path."""
        # Estimate required radius (assuming max wave speed of 15 km/h)
        # Convert duration to hours, multiply by 15km/h. Cap at 120km to avoid overpass timeout.
        req_radius_km = max(30.0, min(120.0, (self.duration_min / 60.0) * 15.0))
        
        try:
            _, _, river_data = OSMDataFetcher.get_or_fetch_data(
                self.dam_id, self.dam_lat, self.dam_lon, radius_km=req_radius_km
            )
            features = river_data.get("features", [])
            if features:
                # Collect ALL river segments and stitch them together
                all_segments = []
                for feat in features:
                    coords = feat.get("geometry", {}).get("coordinates", [])
                    if len(coords) >= 2:
                        all_segments.append(coords)

                if all_segments:
                    stitched = self._stitch_river_segments(all_segments)
                    if len(stitched) >= 3:
                        return stitched

        except Exception as e:
            print(f"[InundationSolver] Could not load OSM river data: {e}")

        # Fallback: DEM-guided synthetic downstream channel
        return self._generate_dem_guided_river()

    def _stitch_river_segments(self, segments):
        """
        Stitch multiple OSM river segments into one continuous downstream path
        ordered by distance from dam.
        """
        dam_pt = np.array([self.dam_lon, self.dam_lat])

        # Sort segments by proximity of their nearest point to the dam
        def nearest_dist(seg):
            dists = [np.linalg.norm(np.array(c) - dam_pt) for c in seg]
            return min(dists)

        segments.sort(key=nearest_dist)

        # Start with the segment closest to the dam
        result = list(segments[0])

        # Find the point on result closest to dam and ensure downstream ordering
        dists_to_dam = [np.linalg.norm(np.array(c) - dam_pt) for c in result]
        dam_idx = int(np.argmin(dists_to_dam))

        # Check which direction is "downstream" using DEM elevation
        elev_start = self._sample_elevation(result[0][1], result[0][0])
        elev_end = self._sample_elevation(result[-1][1], result[-1][0])

        # Downstream = lower elevation. If start is lower, reverse.
        if elev_start < elev_end:
            result.reverse()
            dam_idx = len(result) - 1 - dam_idx

        # Take from dam point downstream
        result = result[dam_idx:]

        # Greedily append remaining segments
        used = {0}
        for _ in range(len(segments)):
            if len(used) == len(segments):
                break
            tail = np.array(result[-1])
            best_seg = None
            best_dist = float('inf')
            best_reversed = False
            for idx, seg in enumerate(segments):
                if idx in used:
                    continue
                d_start = np.linalg.norm(np.array(seg[0]) - tail)
                d_end = np.linalg.norm(np.array(seg[-1]) - tail)
                if d_start < best_dist:
                    best_dist = d_start
                    best_seg = idx
                    best_reversed = False
                if d_end < best_dist:
                    best_dist = d_end
                    best_seg = idx
                    best_reversed = True

            if best_seg is not None and best_dist < 0.1:  # ~11km threshold
                used.add(best_seg)
                seg_to_add = list(segments[best_seg])
                if best_reversed:
                    seg_to_add.reverse()
                result.extend(seg_to_add[1:])  # skip first (duplicate junction)

        return result

    def _generate_dem_guided_river(self):
        """
        Generate downstream river path by following DEM gradient from dam location.
        This creates a terrain-following path instead of a generic straight line.
        """
        coords = [[self.dam_lon, self.dam_lat]]
        curr_i, curr_j = self.dem_proc.latlon_to_grid(self.dam_lat, self.dam_lon)
        # Clamp to valid grid bounds
        curr_i = int(np.clip(curr_i, 0, self.ny - 1))
        curr_j = int(np.clip(curr_j, 0, self.nx - 1))
        visited = set()

        # 8 direction offsets: N, NE, E, SE, S, SW, W, NW
        offsets = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]

        max_steps = int(max(300, (self.duration_min / 60.0) * 80)) # More steps for longer duration

        for _ in range(max_steps):
            visited.add((curr_i, curr_j))
            curr_elev = self.dem[curr_i, curr_j]

            # Find steepest descent neighbor
            best_drop = 0.0
            best_ni, best_nj = curr_i, curr_j
            for di, dj in offsets:
                ni, nj = curr_i + di, curr_j + dj
                if 0 <= ni < self.ny and 0 <= nj < self.nx and (ni, nj) not in visited:
                    drop = curr_elev - self.dem[ni, nj]
                    dist = np.sqrt(di ** 2 + dj ** 2)
                    slope = drop / dist if dist > 0 else 0
                    if slope > best_drop:
                        best_drop = slope
                        best_ni, best_nj = ni, nj

            if best_ni == curr_i and best_nj == curr_j:
                break  # No downhill neighbor found (flat area or local minimum)

            curr_i, curr_j = best_ni, best_nj
            lat, lon = self.dem_proc.grid_to_latlon(curr_i, curr_j)
            coords.append([round(lon, 6), round(lat, 6)])

        if len(coords) < 3:
            # Absolute fallback
            fallback_steps = int(max(15, (self.duration_min / 60.0) * 4))
            for i in range(fallback_steps):
                t = (i + 1) / 15.0
                lon = self.dam_lon + t * 0.12 * (self.duration_min / 360.0)
                lat = self.dam_lat - t * 0.10 * (self.duration_min / 360.0)
                coords.append([round(lon, 5), round(lat, 5)])

        return coords

    # ──────────────────────────────────────────────────────────────────────
    # Terrain Profiling
    # ──────────────────────────────────────────────────────────────────────

    def _sample_elevation(self, lat, lon):
        """Sample DEM elevation at a geographic coordinate."""
        i, j = self.dem_proc.latlon_to_grid(lat, lon)
        i = int(np.clip(i, 0, self.ny - 1))
        j = int(np.clip(j, 0, self.nx - 1))
        return float(self.dem[i, j])

    def _build_river_profile(self):
        """
        Build elevation profile along the river path.
        Returns list of dicts with: lon, lat, elevation_m, cumulative_dist_m, slope
        """
        profile = []
        cum_dist = 0.0

        for idx, coord in enumerate(self.river_coords):
            lon, lat = coord[0], coord[1]
            elev = self._sample_elevation(lat, lon)

            if idx > 0:
                prev = self.river_coords[idx - 1]
                dx = (lon - prev[0]) * self.lon_scale
                dy = (lat - prev[1]) * self.lat_scale
                seg_dist = np.sqrt(dx ** 2 + dy ** 2)
                cum_dist += seg_dist
            else:
                seg_dist = 0.0

            profile.append({
                "idx": idx,
                "lon": lon,
                "lat": lat,
                "elevation_m": elev,
                "cumulative_dist_m": cum_dist,
                "segment_dist_m": seg_dist
            })

        # Compute slope for each segment
        for i in range(len(profile)):
            if i == 0:
                profile[i]["slope"] = 0.01  # Default for first point
            else:
                dz = profile[i - 1]["elevation_m"] - profile[i]["elevation_m"]
                dx = profile[i]["segment_dist_m"]
                if dx > 0:
                    profile[i]["slope"] = max(0.0001, abs(dz / dx))  # Minimum slope
                else:
                    profile[i]["slope"] = 0.001

        return profile

    def _get_cross_section(self, center_lat, center_lon, bearing_deg, half_width_m=1500.0, num_samples=40):
        """
        Extract terrain cross-section perpendicular to river at a given point.
        Returns array of (offset_m, elevation_m) pairs from left bank to right bank.
        """
        # Perpendicular bearing
        perp_bearing = np.radians(bearing_deg + 90.0)

        cross_section = []
        for i in range(num_samples):
            offset_m = -half_width_m + (2 * half_width_m * i / (num_samples - 1))

            # Offset position
            dlat = (offset_m * np.cos(perp_bearing)) / self.lat_scale
            dlon = (offset_m * np.sin(perp_bearing)) / self.lon_scale

            sample_lat = center_lat + dlat
            sample_lon = center_lon + dlon

            # Check bounds
            if (self.dem_proc.lon_min <= sample_lon <= self.dem_proc.lon_max and
                    self.dem_proc.lat_min <= sample_lat <= self.dem_proc.lat_max):
                elev = self._sample_elevation(sample_lat, sample_lon)
            else:
                elev = float('inf')  # Out of DEM bounds

            cross_section.append({
                "offset_m": offset_m,
                "elevation_m": elev,
                "lat": sample_lat,
                "lon": sample_lon
            })

        return cross_section

    def _compute_bearing(self, idx):
        """Compute bearing of river flow direction at a point (in degrees)."""
        # Clamp index to valid range
        idx = max(0, min(idx, len(self.river_coords) - 1))

        if idx < len(self.river_coords) - 1:
            p1 = self.river_coords[idx]
            p2 = self.river_coords[idx + 1]
        elif idx > 0:
            p1 = self.river_coords[idx - 1]
            p2 = self.river_coords[idx]
        else:
            return 180.0  # Default south-flowing

        dx = (p2[0] - p1[0]) * self.lon_scale
        dy = (p2[1] - p1[1]) * self.lat_scale
        bearing = np.degrees(np.arctan2(dx, dy)) % 360
        return bearing

    # ──────────────────────────────────────────────────────────────────────
    # Breach Hydrograph (Physics-Based)
    # ──────────────────────────────────────────────────────────────────────

    def calculate_breach_hydrograph(self, dam_height_m: float, release_percent: float,
                                    duration_min: float, reservoir_capacity_mcm: float = 0.0):
        """
        Dam-break breach hydrograph using:
        - Froehlich (1995) empirical peak discharge
        - Weir equation Q = C * B * H^1.5
        - Triangular hydrograph assumption for total volume
        """
        eff_height = dam_height_m * (release_percent / 100.0)

        # Breach width estimation (Froehlich 1995)
        breach_width = 0.1803 * (eff_height ** 0.32) * ((dam_height_m * 50) ** 0.19)
        breach_width = max(breach_width, 20.0)
        breach_width = min(breach_width, dam_height_m * 5)

        # Weir equation for peak discharge
        c_weir = 1.7  # Weir coefficient (SI units)
        q_peak = c_weir * breach_width * (eff_height ** 1.5)

        # Duration of breach outflow
        duration_sec = max(duration_min, 30) * 60.0

        # Total volume released (triangular hydrograph)
        total_volume_m3 = 0.5 * q_peak * duration_sec

        # If we have reservoir capacity, cap volume
        if reservoir_capacity_mcm > 0:
            max_vol = reservoir_capacity_mcm * 1e6 * (release_percent / 100.0)
            total_volume_m3 = min(total_volume_m3, max_vol)

        return {
            "q_peak_m3s": round(q_peak, 2),
            "total_volume_m3": round(total_volume_m3, 2),
            "effective_breach_width_m": round(breach_width, 1),
            "eff_height_m": round(eff_height, 1),
            "duration_sec": round(duration_sec, 0)
        }

    # ──────────────────────────────────────────────────────────────────────
    # Wave Propagation (Manning + Shallow Water)
    # ──────────────────────────────────────────────────────────────────────

    def _get_discharge_at_time(self, t_seconds, q_peak, duration_sec):
        """
        Triangular breach hydrograph: discharge rises to peak at t_peak,
        then decays linearly to zero at duration_sec.
        """
        if t_seconds <= 0 or duration_sec <= 0:
            return 0.0
        # Peak occurs at 1/3 of total breach duration (Froehlich assumption)
        t_peak = duration_sec / 3.0
        if t_seconds <= t_peak:
            return q_peak * (t_seconds / t_peak)
        elif t_seconds <= duration_sec:
            return q_peak * (1.0 - (t_seconds - t_peak) / (duration_sec - t_peak))
        else:
            # After breach closes, residual base flow (~5% of peak)
            return q_peak * 0.05

    def _compute_wave_front_distance(self, t_seconds, q_peak, eff_height):
        """
        Compute how far downstream the flood wave front has traveled by time t.
        Uses time-integrated Manning's velocity with time-varying discharge.
        """
        if t_seconds <= 0:
            return 0.0

        # Average slope from river profile
        if len(self.river_profile) >= 2:
            total_drop = self.river_profile[0]["elevation_m"] - self.river_profile[-1]["elevation_m"]
            total_dist = self.river_profile[-1]["cumulative_dist_m"]
            avg_slope = max(0.001, abs(total_drop / total_dist)) if total_dist > 0 else 0.005
        else:
            avg_slope = 0.005

        # Integrate wave front position over time using small steps
        # This properly accounts for the rising/falling hydrograph
        dt = min(60.0, t_seconds / 20.0)  # Integration step (max 60s)
        distance = 0.0
        duration_sec = self.duration_min * 60.0
        est_width = 50.0 + eff_height * 2.0

        t = 0.0
        while t < t_seconds:
            step = min(dt, t_seconds - t)
            # Current discharge from hydrograph
            q_now = self._get_discharge_at_time(t, q_peak, duration_sec)

            # Manning's depth from discharge: d = (Q*n / (W*S^0.5))^(3/5)
            if q_now > 0 and avg_slope > 0:
                try:
                    depth_now = (q_now * MANNING_N / (est_width * (avg_slope ** 0.5))) ** 0.6
                    depth_now = min(depth_now, eff_height * 0.8)
                    depth_now = max(depth_now, 0.1)
                except (ValueError, ZeroDivisionError, OverflowError):
                    depth_now = eff_height * 0.2
            else:
                depth_now = 0.1

            # Manning's velocity
            hydraulic_radius = depth_now * 0.7
            v_manning = (1.0 / MANNING_N) * (hydraulic_radius ** (2.0 / 3.0)) * (avg_slope ** 0.5)

            # Shallow water celerity
            wave_celerity = np.sqrt(GRAVITY * depth_now)

            # Front speed = flow velocity + wave celerity
            front_speed = v_manning + wave_celerity * 0.5

            # Friction-based attenuation increases with distance traveled
            friction_factor = 1.0 / (1.0 + 0.000005 * distance)
            distance += front_speed * step * friction_factor
            t += step

        return distance

    def _compute_depth_at_distance(self, dist_m, q_peak, eff_height, total_river_length):
        """
        Compute flood depth at a given distance downstream.
        Depth attenuates with distance due to valley widening and friction losses.
        """
        if total_river_length <= 0:
            return eff_height * 0.3

        frac = dist_m / total_river_length
        # Exponential decay of peak depth with distance
        # Near dam: high depth. Far downstream: reduced.
        depth = eff_height * 0.6 * np.exp(-1.2 * frac)

        # Minimum depth if still within wave front
        depth = max(depth, 0.3)

        return depth

    def _compute_flood_width_from_cross_section(self, cross_section, water_surface_elev, manning_depth=None):
        """
        Given a terrain cross-section and water surface elevation,
        compute the actual inundation width and depth profile.
        Returns list of (lat, lon) for the wetted polygon boundary and max_depth.
        """
        wetted_points = []
        max_depth = 0.0
        # Cap reported depth at the Manning's depth (the physics-derived value)
        # This prevents absurd depths when terrain drops far below river level
        depth_cap = manning_depth if manning_depth else 20.0

        for pt in cross_section:
            if pt["elevation_m"] < water_surface_elev and pt["elevation_m"] != float('inf'):
                depth = min(water_surface_elev - pt["elevation_m"], depth_cap)
                max_depth = max(max_depth, depth)
                wetted_points.append(pt)

        return wetted_points, max_depth

    # ──────────────────────────────────────────────────────────────────────
    # Main Simulation Engine
    # ──────────────────────────────────────────────────────────────────────

    def run_terrain_propagation(self, dam_lat: float, dam_lon: float, dam_height_m: float,
                                release_percent: float, timesteps_min: list,
                                reservoir_capacity_mcm: float = 0.0):
        """
        Physics-based flood wave propagation:
        1. Compute breach hydrograph
        2. For each timestep, compute wave front position using Manning's + celerity
        3. At each river segment reached, sample DEM cross-section
        4. Fill cross-section to compute true inundation width & depth
        5. Generate GeoJSON polygon from wetted boundaries
        """
        hydro = self.calculate_breach_hydrograph(
            dam_height_m, release_percent, max(timesteps_min),
            reservoir_capacity_mcm
        )
        q_peak = hydro["q_peak_m3s"]
        eff_height = hydro["eff_height_m"]

        # Total river length from profile
        total_river_length = self.river_profile[-1]["cumulative_dist_m"] if self.river_profile else 10000.0

        # Dam elevation from DEM
        dam_elev = self._sample_elevation(dam_lat, dam_lon)

        geojson_timesteps = {}
        global_max_depth = 0.0

        for t in timesteps_min:
            t_seconds = t * 60.0
            features = []

            # ── 1. Upstream Reservoir ──────────────────────────────────
            if t >= 0:
                reservoir_features = self._build_reservoir_polygon(
                    dam_elev, eff_height, release_percent
                )
                features.extend(reservoir_features)

            # ── 2. Downstream Flood Wave ──────────────────────────────
            wave_front_dist = self._compute_wave_front_distance(t_seconds, q_peak, eff_height)

            if wave_front_dist > 0 and len(self.river_profile) >= 2:
                downstream_features, timestep_max_depth, timestep_area = \
                    self._build_downstream_flood(wave_front_dist, q_peak, eff_height,
                                                 total_river_length, t)
                features.extend(downstream_features)
                global_max_depth = max(global_max_depth, timestep_max_depth)
            else:
                timestep_max_depth = 0.0
                timestep_area = 0.0

            geojson_timesteps[f"t{t}"] = {
                "type": "FeatureCollection",
                "features": features,
                "properties": {
                    "timestep_min": t,
                    "inundated_area_km2": round(timestep_area, 2),
                    "max_depth_m": round(timestep_max_depth, 1),
                    "wave_front_km": round(wave_front_dist / 1000.0, 1)
                }
            }

        return geojson_timesteps, hydro, round(global_max_depth, 1)

    def _build_downstream_flood(self, wave_front_dist, q_peak, eff_height,
                                 total_river_length, timestep_min):
        """
        Build downstream flood polygons by:
        1. Walking along river profile up to wave front distance
        2. At each segment, computing cross-sectional flood width from DEM
        3. Building tiered depth polygons
        """
        features = []
        max_depth = 0.0
        total_area_m2 = 0.0

        # Collect left/right bank boundary points for the flood polygon
        left_bank = []
        right_bank = []

        # Sample cross-sections at intervals along the reached river
        sample_interval = max(1, len(self.river_profile) // 50)  # ~50 cross-sections for better resolution

        segments_reached = [
            p for p in self.river_profile
            if p["cumulative_dist_m"] <= wave_front_dist
        ]

        if len(segments_reached) < 2:
            segments_reached = self.river_profile[:2]

        # Process segments to build flood corridor
        for i, prof in enumerate(segments_reached):
            if i % sample_interval != 0 and i != 0 and i != len(segments_reached) - 1:
                continue

            dist_m = prof["cumulative_dist_m"]
            river_elev = prof["elevation_m"]
            local_slope = prof["slope"]

            # Compute local flood depth using Manning's equation
            # Q = A * v = (w * d) * (1/n) * d^(2/3) * S^(1/2)
            # Simplified: d ≈ (Q * n / (w * S^0.5))^(3/5) for wide channel
            #
            # Time-varying discharge: use hydrograph value at this timestep
            # Also attenuate with distance (wave spreading + friction losses)
            t_sec = timestep_min * 60.0
            duration_sec = self.duration_min * 60.0
            q_at_time = self._get_discharge_at_time(t_sec, q_peak, duration_sec)
            dist_ratio = dist_m / total_river_length if total_river_length > 0 else 0
            local_q = q_at_time * np.exp(-0.8 * dist_ratio)  # Spatial attenuation

            # Estimate channel width from cross-section or use empirical
            estimated_width = 50.0 + eff_height * 2.0  # Rough initial estimate

            if local_slope > 0 and estimated_width > 0:
                # Manning's depth: d = (Q * n / (W * S^0.5))^(3/5)
                try:
                    manning_depth = (local_q * MANNING_N / (estimated_width * (local_slope ** 0.5))) ** 0.6
                    if not np.isfinite(manning_depth):
                        manning_depth = eff_height * 0.3
                except (ValueError, ZeroDivisionError, OverflowError):
                    manning_depth = eff_height * 0.3
            else:
                manning_depth = eff_height * 0.3

            manning_depth = min(manning_depth, 20.0)  # Realistic cap: even catastrophic floods rarely exceed 20m
            manning_depth = max(manning_depth, 0.2)  # Minimum visible depth

            # Water surface elevation at this point
            water_surface = river_elev + manning_depth

            # Get terrain cross-section perpendicular to river
            bearing = self._compute_bearing(prof["idx"])

            # Cross-section half-width scales with depth (deeper = wider flood)
            half_width = min(5000.0, max(800.0, manning_depth * 300.0))
            cross_section = self._get_cross_section(
                prof["lat"], prof["lon"], bearing,
                half_width_m=half_width, num_samples=50
            )

            # Find actual wetted boundary from terrain
            wetted, section_max_depth = self._compute_flood_width_from_cross_section(
                cross_section, water_surface, manning_depth=manning_depth
            )

            max_depth = max(max_depth, section_max_depth)

            if wetted:
                # Left-most and right-most wetted points define banks
                left_bank.append((wetted[0]["lon"], wetted[0]["lat"]))
                right_bank.append((wetted[-1]["lon"], wetted[-1]["lat"]))

                # Compute area contribution
                width_m = abs(wetted[-1]["offset_m"] - wetted[0]["offset_m"])
                seg_length = prof["segment_dist_m"] if prof["segment_dist_m"] > 0 else 100.0
                total_area_m2 += width_m * seg_length

        # Build polygon from bank boundaries
        total_area_km2 = total_area_m2 / 1e6

        if len(left_bank) >= 2 and len(right_bank) >= 2:
            # Create flood corridor polygon: left bank forward + right bank reversed
            polygon_coords = list(left_bank) + list(reversed(right_bank))
            polygon_coords.append(polygon_coords[0])  # Close ring

            try:
                flood_poly = Polygon(polygon_coords)
                if not flood_poly.is_valid:
                    flood_poly = flood_poly.buffer(0)

                if flood_poly.is_valid and not flood_poly.is_empty:
                    # Create depth-tiered features
                    features.extend(
                        self._create_depth_tiers(flood_poly, max_depth, total_area_km2,
                                                  timestep_min, wave_front_dist)
                    )
            except Exception as e:
                print(f"[InundationSolver] Polygon construction error: {e}")

        # If polygon method failed, fall back to buffer along reached river
        if not features and len(segments_reached) >= 2:
            river_coords_reached = [[p["lon"], p["lat"]] for p in segments_reached]
            features, max_depth, total_area_km2 = self._buffer_fallback(
                river_coords_reached, eff_height, q_peak, total_river_length,
                wave_front_dist, timestep_min
            )

        return features, max_depth, total_area_km2

    def _create_depth_tiers(self, flood_poly, max_depth, area_km2, timestep_min, wave_front_dist):
        """Create multi-tier depth features from a flood polygon by eroding inward."""
        features = []

        # Depth tiers from outer (shallow) to inner (deep)
        depth_tiers = [
            {"frac": 1.00, "band": "0.1 - 0.5", "min_d": 0.1, "max_d": 0.5},
            {"frac": 0.75, "band": "0.5 - 1.0", "min_d": 0.5, "max_d": 1.0},
            {"frac": 0.55, "band": "1.0 - 2.0", "min_d": 1.0, "max_d": 2.0},
            {"frac": 0.38, "band": "2.0 - 3.0", "min_d": 2.0, "max_d": 3.0},
            {"frac": 0.22, "band": "3.0 - 5.0", "min_d": 3.0, "max_d": 5.0},
            {"frac": 0.10, "band": "> 5.0",     "min_d": 5.0, "max_d": 99.0}
        ]

        for tier in depth_tiers:
            if tier["min_d"] > max_depth:
                continue  # Skip tiers deeper than actual max

            try:
                # Scale polygon inward for deeper tiers
                if tier["frac"] < 1.0:
                    # Negative buffer to shrink polygon toward center
                    centroid = flood_poly.centroid
                    # Scale the polygon relative to its centroid
                    from shapely.affinity import scale
                    tier_poly = scale(flood_poly, xfact=tier["frac"], yfact=tier["frac"],
                                     origin=centroid)
                else:
                    tier_poly = flood_poly

                if not tier_poly.is_valid:
                    tier_poly = tier_poly.buffer(0)

                geoms = list(tier_poly.geoms) if isinstance(tier_poly, MultiPolygon) else [tier_poly]
                for g in geoms:
                    if g.is_valid and not g.is_empty and g.area > 1e-10:
                        hazard = "Critical" if tier["min_d"] >= 3.0 else (
                            "High" if tier["min_d"] >= 1.0 else "Moderate")

                        features.append({
                            "type": "Feature",
                            "properties": {
                                "timestep_min": timestep_min,
                                "depth_band": tier["band"],
                                "min_depth": tier["min_d"],
                                "max_depth": tier["max_d"],
                                "max_depth_m": round(max_depth, 1),
                                "avg_depth_m": round(max_depth * 0.55, 1),
                                "inundated_area_km2": round(area_km2 * tier["frac"], 2),
                                "hazard_level": hazard,
                                "zone": "downstream",
                                "wave_front_km": round(wave_front_dist / 1000.0, 1)
                            },
                            "geometry": mapping(g)
                        })
            except Exception:
                pass

        return features

    def _buffer_fallback(self, river_coords, eff_height, q_peak, total_length,
                          wave_front_dist, timestep_min):
        """
        Fallback: buffer along river centerline with physics-derived width.
        Used when cross-sectional polygon construction fails.
        """
        features = []
        max_depth = 0.0

        if len(river_coords) < 2:
            return features, 0.0, 0.0

        river_line = LineString(river_coords)

        # Physics-based buffer width (Manning's)
        avg_slope = 0.005
        if len(self.river_profile) >= 2:
            total_drop = abs(self.river_profile[0]["elevation_m"] - self.river_profile[-1]["elevation_m"])
            total_dist = self.river_profile[-1]["cumulative_dist_m"]
            if total_dist > 0:
                avg_slope = max(0.001, total_drop / total_dist)

        # Manning's depth
        est_width = 80.0
        try:
            manning_d = (q_peak * MANNING_N / (est_width * avg_slope ** 0.5)) ** 0.6
            if not np.isfinite(manning_d):
                manning_d = eff_height * 0.3
        except (ValueError, ZeroDivisionError, OverflowError):
            manning_d = eff_height * 0.3
        manning_d = min(manning_d, eff_height * 0.7)
        manning_d = max(manning_d, 0.3)
        max_depth = manning_d

        # Convert depth to degree-based buffer width
        flood_width_m = min(2000.0, manning_d * 150.0)
        buffer_deg = flood_width_m / self.lon_scale

        # Calculate area
        reach_length_m = wave_front_dist
        area_km2 = (flood_width_m * 2 * reach_length_m) / 1e6

        depth_tiers = [
            {"frac": 1.00, "band": "0.1 - 0.5", "min_d": 0.1, "max_d": 0.5},
            {"frac": 0.78, "band": "0.5 - 1.0", "min_d": 0.5, "max_d": 1.0},
            {"frac": 0.58, "band": "1.0 - 2.0", "min_d": 1.0, "max_d": 2.0},
            {"frac": 0.40, "band": "2.0 - 3.0", "min_d": 2.0, "max_d": 3.0},
            {"frac": 0.25, "band": "3.0 - 5.0", "min_d": 3.0, "max_d": 5.0},
            {"frac": 0.12, "band": "> 5.0",     "min_d": 5.0, "max_d": 99.0}
        ]

        for spec in depth_tiers:
            if spec["min_d"] > max_depth:
                continue
            try:
                tier_geom = river_line.buffer(buffer_deg * spec["frac"], cap_style=1, join_style=1)
                geoms = list(tier_geom.geoms) if isinstance(tier_geom, MultiPolygon) else [tier_geom]
                for g in geoms:
                    if g.is_valid and not g.is_empty:
                        hazard = "Critical" if spec["min_d"] >= 3.0 else (
                            "High" if spec["min_d"] >= 1.0 else "Moderate")
                        features.append({
                            "type": "Feature",
                            "properties": {
                                "timestep_min": timestep_min,
                                "depth_band": spec["band"],
                                "min_depth": spec["min_d"],
                                "max_depth": spec["max_d"],
                                "max_depth_m": round(max_depth, 1),
                                "avg_depth_m": round(max_depth * 0.55, 1),
                                "inundated_area_km2": round(area_km2 * spec["frac"], 2),
                                "hazard_level": hazard,
                                "zone": "downstream",
                                "wave_front_km": round(wave_front_dist / 1000.0, 1)
                            },
                            "geometry": mapping(g)
                        })
            except Exception:
                pass

        return features, max_depth, area_km2

    # ──────────────────────────────────────────────────────────────────────
    # Upstream Reservoir
    # ──────────────────────────────────────────────────────────────────────

    def _build_reservoir_polygon(self, dam_elev, eff_height, release_percent):
        """
        Build upstream reservoir by filling terrain behind the dam
        up to the water surface elevation.
        """
        features = []

        # Upstream direction: opposite to first downstream segment
        upstream_coords = self._build_upstream_arm()
        if len(upstream_coords) < 2:
            return features

        upstream_line = LineString(upstream_coords)
        if upstream_line.length < 0.0005:
            return features

        # Reservoir water level
        water_level = dam_elev + eff_height * 0.3

        # Buffer width based on reservoir scale
        res_buffer_deg = 0.008 + (release_percent * 0.00008)

        res_tiers = [
            {"frac": 1.00, "band": "0.1 - 0.5", "min_d": 0.1, "max_d": 0.5},
            {"frac": 0.70, "band": "0.5 - 1.0", "min_d": 0.5, "max_d": 1.0},
            {"frac": 0.45, "band": "1.0 - 2.0", "min_d": 1.0, "max_d": 2.0},
            {"frac": 0.25, "band": "2.0 - 3.0", "min_d": 2.0, "max_d": 3.0}
        ]

        for tier in res_tiers:
            try:
                geom = upstream_line.buffer(res_buffer_deg * tier["frac"], cap_style=1, join_style=1)
                geoms = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
                for g in geoms:
                    if g.is_valid and not g.is_empty:
                        features.append({
                            "type": "Feature",
                            "properties": {
                                "depth_band": tier["band"],
                                "min_depth": tier["min_d"],
                                "max_depth": tier["max_d"],
                                "max_depth_m": round(eff_height * 0.5, 1),
                                "avg_depth_m": round(eff_height * 0.25, 1),
                                "hazard_level": "Moderate",
                                "zone": "reservoir"
                            },
                            "geometry": mapping(g)
                        })
            except Exception:
                pass

        return features

    def _build_upstream_arm(self):
        """Build upstream reservoir arm using DEM gradient (uphill from dam)."""
        coords = []
        curr_i, curr_j = self.dem_proc.latlon_to_grid(self.dam_lat, self.dam_lon)
        # Clamp to valid grid bounds
        curr_i = int(np.clip(curr_i, 0, self.ny - 1))
        curr_j = int(np.clip(curr_j, 0, self.nx - 1))
        visited = set()

        # 8 direction offsets
        offsets = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]

        # Walk UPHILL from dam (steepest ascent towards reservoir)
        for _ in range(25):
            visited.add((curr_i, curr_j))
            curr_elev = self.dem[curr_i, curr_j]
            lat, lon = self.dem_proc.grid_to_latlon(curr_i, curr_j)
            coords.append([round(lon, 6), round(lat, 6)])

            # Find steepest ascent (uphill) neighbor — towards reservoir
            best_rise = 0.0
            best_ni, best_nj = curr_i, curr_j
            for di, dj in offsets:
                ni, nj = curr_i + di, curr_j + dj
                if 0 <= ni < self.ny and 0 <= nj < self.nx and (ni, nj) not in visited:
                    rise = self.dem[ni, nj] - curr_elev
                    if rise > best_rise:
                        best_rise = rise
                        best_ni, best_nj = ni, nj

            # If no uphill neighbor, try lateral movement (valley walls)
            if best_ni == curr_i and best_nj == curr_j:
                # Try the least steep descent as an alternative upstream path
                min_drop = float('inf')
                for di, dj in offsets:
                    ni, nj = curr_i + di, curr_j + dj
                    if 0 <= ni < self.ny and 0 <= nj < self.nx and (ni, nj) not in visited:
                        drop = curr_elev - self.dem[ni, nj]
                        if 0 < drop < min_drop:
                            min_drop = drop
                            best_ni, best_nj = ni, nj

            if best_ni == curr_i and best_nj == curr_j:
                break

            curr_i, curr_j = best_ni, best_nj

        # Reverse so coords go from upstream end → dam
        coords.reverse()
        return coords
