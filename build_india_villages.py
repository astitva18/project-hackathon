"""Build ResQLink's India village database from the PMGSY rural habitations open dataset.

Source  : PMGSY (Pradhan Mantri Gram Sadak Yojana) habitations, geosadak-pmgsy.nic.in/OpenData,
          Government Open Data License – India. Packaged by ramSeraph/indian_admin_boundaries
          (release "habitations": PMGSY_Habitations.geojsonl.7z, PMGSY_Masterdata.csv, PMGSY_Masterdata.corrections.csv).
Output  : backend/data/india_habitations.tsv.gz  — all ~1.04 million habitations (backend, offline search)
          frontend/vendor/india_villages.txt      — habitations with population >= 3000 (standalone file)

Usage   : python tools/build_india_villages.py <PMGSY_Habitations.geojsonl> <PMGSY_Masterdata.csv> [<corrections.csv>]
          python tools/build_india_villages.py --grid      (only rebuild frontend/vendor/district_grid.txt)
"""
import csv
import gzip
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SMALL_MIN_POP = 3000


def main(hab_path, master_path, corr_path=None):
    states, districts, blocks = {}, {}, {}
    rows = list(csv.DictReader(open(master_path, encoding="utf-8")))
    if corr_path:
        rows += [r for r in csv.DictReader(open(corr_path, encoding="utf-8")) if r.get("ACTION") == "ADD"]
    for r in rows:
        clean = lambda x: " ".join(x.replace("\t", " ").split())
        states[int(r["STATE_ID"])] = clean(r["STATE_NAME"])
        districts[int(r["DISTRICT_ID"])] = clean(r["DISTRICT_NAME"])
        blocks[int(r["BLOCK_ID"])] = clean(r["BLOCK_NAME"])

    habs, seen = [], set()
    with open(hab_path, encoding="utf-8") as f:
        for line in f:
            ft = json.loads(line)
            p, g = ft["properties"], ft.get("geometry") or {}
            c = g.get("coordinates")
            name = (p.get("HAB_NAME") or "").strip()
            if not c or not name:
                continue
            lon, lat = float(c[0]), float(c[1])
            if not (6 < lat < 37.6 and 68 < lon < 97.6):
                continue
            k = (name.lower(), round(lat, 4), round(lon, 4))
            if k in seen:
                continue
            seen.add(k)
            name = " ".join(name.replace("\t", " ").split())
            habs.append([name, p.get("STATE_ID"), p.get("DISTRICT_I"), p.get("BLOCK_ID"), lat, lon, int(p.get("TOT_POPULA") or 0)])

    # fill district/block names missing from the master list with the nearest habitation (same state) that has them
    grid = {}
    for h in habs:
        if h[2] in districts:
            grid.setdefault((h[1], int(h[4] * 10), int(h[5] * 10)), []).append(h)
    fixed = 0
    for h in habs:
        if h[2] in districts:
            continue
        best, bd = None, 1e9
        for r in range(1, 6):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    for o in grid.get((h[1], int(h[4] * 10) + dx, int(h[5] * 10) + dy), []):
                        d = (o[4] - h[4]) ** 2 + ((o[5] - h[5]) * math.cos(math.radians(h[4]))) ** 2
                        if d < bd:
                            best, bd = o, d
            if best:
                break
        if best:
            h[2] = best[2]
            if h[3] not in blocks:
                h[3] = best[3]
            fixed += 1

    out = ROOT / "backend" / "data" / "india_habitations.tsv.gz"
    with gzip.open(out, "wt", encoding="utf-8", compresslevel=9) as o:
        o.write("name\tstate\tdistrict\tblock\tlat\tlon\tpop\n")
        for n, s, d, b, la, lo, pop in habs:
            o.write(f"{n}\t{states.get(s, '')}\t{districts.get(d, '')}\t{blocks.get(b, '')}\t{la:.5f}\t{lo:.5f}\t{pop}\n")

    small = sorted((h for h in habs if h[6] >= SMALL_MIN_POP), key=lambda h: -h[6])
    dlist = sorted({(districts.get(h[2], ""), states.get(h[1], "")) for h in small})
    di = {d: i for i, d in enumerate(dlist)}
    sm = ROOT / "frontend" / "vendor" / "india_villages.txt"
    with open(sm, "w", encoding="utf-8") as o:
        o.write("|".join(f"{d}~{s}" for d, s in dlist) + "\n")
        for n, s, d, b, la, lo, pop in small:
            o.write(f"{n.replace(chr(9), ' ')}\t{di[(districts.get(d, ''), states.get(s, ''))]}\t{la:.4f}\t{lo:.4f}\t{pop}\n")
    print(f"{len(habs):,} habitations ({fixed:,} district names filled from neighbours) → {out.name} {out.stat().st_size // 1024} KB")
    print(f"{len(small):,} habitations ≥{SMALL_MIN_POP} → {sm.name} {sm.stat().st_size // 1024} KB")





def build_district_grid():
    """frontend/vendor/district_grid.txt: the district (by population) of every 0.1° cell in India — offline district lookup."""
    cells = {}
    with gzip.open(ROOT / "backend" / "data" / "india_habitations.tsv.gz", "rt", encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) != 7 or not p[2]:
                continue
            k = (round(float(p[4]) * 10), round(float(p[5]) * 10))
            c = cells.setdefault(k, {})
            c[(p[2], p[1])] = c.get((p[2], p[1]), 0) + max(1, int(p[6] or 0))
    dlist = sorted({d for c in cells.values() for d in c})
    di = {d: i for i, d in enumerate(dlist)}
    out = ROOT / "frontend" / "vendor" / "district_grid.txt"
    with open(out, "w", encoding="utf-8") as o:
        o.write("|".join(f"{d}~{s}" for d, s in dlist) + "\n")
        for (la, lo), c in sorted(cells.items()):
            o.write(f"{la} {lo} {di[max(c, key=c.get)]}\n")
    print(f"{len(cells):,} cells, {len(dlist)} districts → {out.name} {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--grid":
        build_district_grid()
    elif len(sys.argv) < 3:
        sys.exit(__doc__)
    else:
        main(*sys.argv[1:4])
        build_district_grid()
