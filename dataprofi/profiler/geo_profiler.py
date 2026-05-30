from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from dataprofi.core.config import Config
from dataprofi.core.types import GeoColumnProfile, GeoReport

_config = Config()

LAT_PATTERNS = {"lat", "latitude", "y", "lat_", "_lat", "location_latitude"}
LNG_PATTERNS = {"lng", "lon", "long", "longitude", "x", "lng_", "_lng", "location_longitude"}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return float(r * 2 * np.arcsin(np.sqrt(a)))


def _haversine_array(lats: np.ndarray, lngs: np.ndarray, ref_lat: float, ref_lng: float) -> np.ndarray:
    r = 6371.0
    lats_r = np.radians(lats)
    lngs_r = np.radians(lngs)
    ref_lat_r = np.radians(ref_lat)
    ref_lng_r = np.radians(ref_lng)
    dlat = lats_r - ref_lat_r
    dlon = lngs_r - ref_lng_r
    a = np.sin(dlat / 2) ** 2 + np.cos(ref_lat_r) * np.cos(lats_r) * np.sin(dlon / 2) ** 2
    return r * 2 * np.arcsin(np.sqrt(a))


def _detect_geo_columns(df: pd.DataFrame) -> list[tuple[str, str]]:
    lat_cols = []
    lng_cols = []

    for col in df.columns:
        col_lower = col.lower().replace(" ", "_")
        if any(p in col_lower for p in LAT_PATTERNS):
            if df[col].dtype.kind in ("i", "f"):
                sample = df[col].dropna().head(20)
                if len(sample) > 0 and sample.between(-90, 90).all():
                    lat_cols.append(col)
        elif any(p in col_lower for p in LNG_PATTERNS):
            if df[col].dtype.kind in ("i", "f"):
                sample = df[col].dropna().head(20)
                if len(sample) > 0 and sample.between(-180, 180).all():
                    lng_cols.append(col)

    pairs = []
    for lat_col in lat_cols:
        for lng_col in lng_cols:
            pairs.append((lat_col, lng_col))
    if not pairs and len(lat_cols) > 0 and len(lng_cols) > 0:
        pairs.append((lat_cols[0], lng_cols[0]))

    return pairs


def _profile_geo_pair(df: pd.DataFrame, lat_col: str, lng_col: str) -> GeoColumnProfile:
    lats = pd.to_numeric(df[lat_col], errors="coerce")
    lngs = pd.to_numeric(df[lng_col], errors="coerce")

    valid_mask = lats.notna() & lngs.notna()
    valid_lats = lats[valid_mask].values
    valid_lngs = lngs[valid_mask].values
    total_points = len(df)
    valid_points = int(valid_mask.sum())

    invalid_reasons = []
    out_of_range_lat = int(((valid_lats < -90) | (valid_lats > 90)).sum())
    out_of_range_lng = int(((valid_lngs < -180) | (valid_lngs > 180)).sum())
    if out_of_range_lat > 0:
        invalid_reasons.append(f"{out_of_range_lat} latitude values out of range (-90 to 90)")
    if out_of_range_lng > 0:
        invalid_reasons.append(f"{out_of_range_lng} longitude values out of range (-180 to 180)")

    null_island = int(((valid_lats == 0) & (valid_lngs == 0)).sum())
    if null_island > 0:
        invalid_reasons.append(f"{null_island} points at (0,0) - possible null island errors")

    range_mask = (valid_lats >= -90) & (valid_lats <= 90) & (valid_lngs >= -180) & (valid_lngs <= 180)
    clean_lats = valid_lats[range_mask]
    clean_lngs = valid_lngs[range_mask]
    invalid_count = total_points - len(clean_lats)

    if len(clean_lats) == 0:
        return GeoColumnProfile(
            column_lat=lat_col,
            column_lng=lng_col,
            total_points=total_points,
            valid_points=0,
            invalid_count=total_points,
            invalid_reasons=["No valid coordinate pairs found"],
            centroid_lat=0.0,
            centroid_lng=0.0,
            bounding_box={},
            spatial_spread_km=0.0,
            density_points_per_sq_km=0.0,
            outlier_count=0,
            outlier_indices=[],
            cluster_count=0,
            clusters=[],
        )

    centroid_lat = float(clean_lats.mean())
    centroid_lng = float(clean_lngs.mean())

    bounding_box = {
        "min_lat": float(clean_lats.min()),
        "max_lat": float(clean_lats.max()),
        "min_lng": float(clean_lngs.min()),
        "max_lng": float(clean_lngs.max()),
    }

    distances = _haversine_array(clean_lats, clean_lngs, centroid_lat, centroid_lng)
    spatial_spread_km = float(distances.std()) if len(distances) > 1 else 0.0

    lat_range_km = _haversine_km(bounding_box["min_lat"], centroid_lng, bounding_box["max_lat"], centroid_lng)
    lng_range_km = _haversine_km(centroid_lat, bounding_box["min_lng"], centroid_lat, bounding_box["max_lng"])
    area_sq_km = max(lat_range_km * lng_range_km, 0.01)
    density = len(clean_lats) / area_sq_km

    outlier_threshold = distances.mean() + _config.spatial_outlier_std * distances.std() if distances.std() > 0 else float("inf")
    outlier_mask = distances > outlier_threshold
    outlier_indices = []
    outlier_details = []
    if outlier_mask.any():
        original_indices = df.index[valid_mask][range_mask][outlier_mask].tolist()
        outlier_distances = distances[outlier_mask]
        for i, idx in enumerate(original_indices[:20]):
            outlier_indices.append(int(idx))
            dist_km = float(outlier_distances[i])
            lat_val = float(df[lat_col].iloc[idx])
            lng_val = float(df[lng_col].iloc[idx])
            outlier_details.append({
                "row": int(idx),
                "latitude": round(lat_val, 6),
                "longitude": round(lng_val, 6),
                "distance_from_centre_km": round(dist_km, 2),
                "reason": (
                    f"This point ({lat_val:.4f}, {lng_val:.4f}) is {dist_km:.1f} km away from the "
                    f"data centre ({centroid_lat:.4f}, {centroid_lng:.4f}). "
                    f"Most points are within {outlier_threshold:.1f} km. "
                    f"This may be a data entry error or a genuinely remote location."
                ),
            })

    cluster_count = 0
    clusters = []
    n_clean = len(clean_lats)
    if n_clean >= 10:
        k = min(5, max(2, n_clean // 20))
        coords = np.column_stack([clean_lats, clean_lngs])
        kmeans = KMeans(n_clusters=k, n_init=5, random_state=42, max_iter=100)
        labels = kmeans.fit_predict(coords)
        cluster_count = k
        for i in range(k):
            mask_i = labels == i
            cluster_lat = round(float(clean_lats[mask_i].mean()), 6)
            cluster_lng = round(float(clean_lngs[mask_i].mean()), 6)
            cluster_spread = float(_haversine_array(
                clean_lats[mask_i], clean_lngs[mask_i], cluster_lat, cluster_lng
            ).mean()) if mask_i.sum() > 1 else 0.0
            clusters.append({
                "centroid_lat": cluster_lat,
                "centroid_lng": cluster_lng,
                "point_count": int(mask_i.sum()),
                "avg_spread_km": round(cluster_spread, 2),
                "label": f"Cluster {i + 1} - {int(mask_i.sum())} points within ~{cluster_spread:.1f} km radius",
            })
        clusters.sort(key=lambda c: c["point_count"], reverse=True)

    return GeoColumnProfile(
        column_lat=lat_col,
        column_lng=lng_col,
        total_points=total_points,
        valid_points=valid_points,
        invalid_count=invalid_count,
        invalid_reasons=invalid_reasons,
        centroid_lat=round(centroid_lat, 6),
        centroid_lng=round(centroid_lng, 6),
        bounding_box=bounding_box,
        spatial_spread_km=round(spatial_spread_km, 2),
        density_points_per_sq_km=round(density, 2),
        outlier_count=int(outlier_mask.sum()),
        outlier_indices=outlier_indices,
        outlier_details=outlier_details,
        cluster_count=cluster_count,
        clusters=clusters,
    )


def profile_geo(df: pd.DataFrame) -> GeoReport:
    pairs = _detect_geo_columns(df)
    if not pairs:
        return GeoReport()
    profiles = [_profile_geo_pair(df, lat, lng) for lat, lng in pairs]
    return GeoReport(detected_pairs=pairs, profiles=profiles)
