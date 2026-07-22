"""
Generate the globe's landmass dot field from Natural Earth 110m land polygons.

Samples a lat/lon grid (denser at the equator via cos-lat spacing), keeps
points that fall on land (pure-python ray casting), writes them as a compact
JSON array of [lat, lon] pairs to ui/os/land-dots.json.

Run once (or whenever you want a different density):
    .venv/bin/python scripts/gen_globe_dots.py path/to/ne_110m_land.json
"""
import json
import math
import sys
from pathlib import Path

STEP_DEG = 1.35          # base grid spacing at the equator
OUT = Path(__file__).resolve().parent.parent / "ui" / "os" / "land-dots.json"


def point_in_ring(lon, lat, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat):
            x_cross = (xj - xi) * (lat - yi) / (yj - yi) + xi
            if lon < x_cross:
                inside = not inside
        j = i
    return inside


def point_in_polygon(lon, lat, polygon):
    """polygon = [outer_ring, hole1, hole2, ...]"""
    if not point_in_ring(lon, lat, polygon[0]):
        return False
    for hole in polygon[1:]:
        if point_in_ring(lon, lat, hole):
            return False
    return True


def main(geojson_path):
    data = json.load(open(geojson_path))
    polygons = []   # list of (bbox, rings)
    for feat in data["features"]:
        geom = feat["geometry"]
        polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        for poly in polys:
            xs = [p[0] for p in poly[0]]
            ys = [p[1] for p in poly[0]]
            polygons.append(((min(xs), min(ys), max(xs), max(ys)), poly))

    dots = []
    lat = -88.0
    while lat <= 88.0:
        # keep on-sphere dot spacing roughly constant: widen lon step at poles
        lon_step = STEP_DEG / max(0.18, math.cos(math.radians(lat)))
        lon = -180.0
        while lon < 180.0:
            for (x0, y0, x1, y1), poly in polygons:
                if x0 <= lon <= x1 and y0 <= lat <= y1:
                    if point_in_polygon(lon, lat, poly):
                        dots.append([round(lat, 2), round(lon, 2)])
                        break
            lon += lon_step
        lat += STEP_DEG

    OUT.write_text(json.dumps(dots, separators=(",", ":")))
    print(f"{len(dots)} land dots → {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main(sys.argv[1])
