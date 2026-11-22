"""Convert MOSDAC INSAT-3DR/3DS rainfall HDF5 files into a daily rainfall CSV that ResQLink can use.

1. Download HDF5 files from mosdac.gov.in (Catalog → Satellite → INSAT-3DR → rainfall product, e.g. 3RIMG_L2B_IMC,
   or with the MOSDAC Data Download API).
2. Inspect one file to find the rain variable and lat/lon variables:
       python tools/hdf5_to_csv.py --inspect FILE.h5
3. Convert a folder of files for one place (nearest pixel, summed per day):
       python tools/hdf5_to_csv.py --lat 11.465 --lon 76.136 --rain-var <RAIN> --lat-var <LAT> --lon-var <LON> \
              --hours-per-file 0.5 --out wayanad_insat.csv  data/*.h5
4. Upload the CSV in the ResQLink command centre (Phase 02 → Upload CSV). With the backend running it is stored and
   automatically replaces reanalysis rain for that area.

Variable names differ between products/versions, which is why they are parameters — check with --inspect.
Rain-rate products are in mm/h: --hours-per-file converts each file's rate to an accumulation (0.5 for half-hourly).
Requires: pip install h5py numpy
"""
import argparse
import collections
import re
import sys

try:
    import h5py
    import numpy as np
except ImportError:
    sys.exit("pip install h5py numpy")


def inspect(path):
    with h5py.File(path, "r") as f:
        f.visititems(lambda n, o: print(f"{n:50s} {getattr(o, 'shape', '')} {getattr(o, 'dtype', '')}") if isinstance(o, h5py.Dataset) else None)


def file_date(path, f):
    m = re.search(r"(\d{2})([A-Z]{3})(\d{4})", path.upper())  # MOSDAC names look like 3RIMG_29JUL2024_0815_...
    if m:
        mon = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split().index(m.group(2)) + 1
        return f"{m.group(3)}-{mon:02d}-{m.group(1)}"
    for k in ("Acquisition_Date", "Nominal_Date", "date"):
        if k in f.attrs:
            return str(f.attrs[k])[:10]
    raise ValueError(f"cannot find date for {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--inspect")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--rain-var")
    ap.add_argument("--lat-var")
    ap.add_argument("--lon-var")
    ap.add_argument("--hours-per-file", type=float, default=0.5)
    ap.add_argument("--fill", type=float, default=-999)
    ap.add_argument("--out", default="insat_rain.csv")
    a = ap.parse_args()
    if a.inspect:
        return inspect(a.inspect)
    if None in (a.lat, a.lon, a.rain_var, a.lat_var, a.lon_var) or not a.files:
        ap.error("need files, --lat, --lon, --rain-var, --lat-var, --lon-var (use --inspect first)")
    daily = collections.defaultdict(float)
    for p in a.files:
        with h5py.File(p, "r") as f:
            la, lo, rr = np.squeeze(f[a.lat_var][()]), np.squeeze(f[a.lon_var][()]), np.squeeze(f[a.rain_var][()]).astype(float)
            if la.ndim == 1:  # regular grid
                i, j = np.abs(la - a.lat).argmin(), np.abs(lo - a.lon).argmin()
                v = rr[i, j]
            else:  # per-pixel lat/lon arrays
                k = np.unravel_index(np.argmin((la - a.lat) ** 2 + (lo - a.lon) ** 2), la.shape)
                v = rr[k]
            if v != a.fill and np.isfinite(v) and v >= 0:
                daily[file_date(p, f)] += v * a.hours_per_file
    with open(a.out, "w") as o:
        o.write(f"latitude,longitude\n{a.lat},{a.lon}\n\ndate,rain_mm\n")
        for d in sorted(daily):
            o.write(f"{d},{daily[d]:.1f}\n")
    print(f"wrote {a.out}: {len(daily)} days")


if __name__ == "__main__":
    main()
