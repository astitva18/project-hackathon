"""Build standalone/ResQLink.html — the command centre as ONE file (no server, works offline, globe included).

Usage (from project root):  python tools/build_standalone.py
"""
import base64
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONT, VEN = ROOT / "frontend", ROOT / "frontend" / "vendor"
s = (FRONT / "index.html").read_text(encoding="utf-8")


def js(name):
    return "<script>" + (VEN / name).read_text(encoding="utf-8").replace("</script>", "<\\/script>") + "</script>"


swaps = {
    '<link rel="stylesheet" href="vendor/leaflet.css">': "<style>" + re.sub(r"url\((images/[\w.-]+\.png)\)", lambda m: "url(data:image/png;base64,"
        + base64.b64encode((VEN / m.group(1)).read_bytes()).decode() + ")", (VEN / "leaflet.css").read_text(encoding="utf-8")) + "</style>",
    '<script src="vendor/leaflet.js"></script>': js("leaflet.js"),
    '<script src="vendor/globe.gl.min.js"></script>': js("globe.gl.min.js"),
    '<script src="vendor/qrcode.js"></script>': js("qrcode.js"),
    '<script src="vendor/shp.min.js"></script>': js("shp.min.js"),
    '<script type="text/plain" id="india-districts" data-src="vendor/india_districts.txt"></script>':
        '<script type="text/plain" id="india-districts" data-src="vendor/india_districts.txt">' + (VEN / "india_districts.txt").read_text(encoding="utf-8") + "</script>",
    '<script type="text/plain" id="dgrid" data-src="vendor/district_grid.txt"></script>':
        '<script type="text/plain" id="dgrid" data-src="vendor/district_grid.txt">' + (VEN / "district_grid.txt").read_text(encoding="utf-8") + "</script>",
    '<script type="text/plain" id="ifi-data" data-src="vendor/ifi.txt"></script>':
        '<script type="text/plain" id="ifi-data" data-src="vendor/ifi.txt">' + (VEN / "ifi.txt").read_text(encoding="utf-8").replace("</", "<\\/") + "</script>",
    '<script src="vendor/chart.umd.js"></script>': js("chart.umd.js"),
    '<script type="text/plain" id="world-places" data-src="vendor/places.txt"></script>':
        '<script type="text/plain" id="world-places" data-src="vendor/places.txt">' + (VEN / "places.txt").read_text(encoding="utf-8").replace("</", "<\\/") + "</script>",
    '<script type="text/plain" id="india-villages" data-src="vendor/india_villages.txt"></script>':
        '<script type="text/plain" id="india-villages" data-src="vendor/india_villages.txt">' + (VEN / "india_villages.txt").read_text(encoding="utf-8").replace("</", "<\\/") + "</script>",
    "const EARTH_IMG='vendor/earth.jpg';": "const EARTH_IMG='data:image/jpeg;base64," + base64.b64encode((VEN / "earth.jpg").read_bytes()).decode() + "';",
}
for a, b in swaps.items():
    if a not in s:
        raise SystemExit(f"build marker not found: {a[:60]}")
    s = s.replace(a, b)
out = ROOT / "standalone" / "ResQLink.html"
out.parent.mkdir(exist_ok=True)
out.write_text(s, encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
