# Put ResQLink online (≈ 20 minutes, free)

Result: a public link like `https://resqlink-xxxx.onrender.com`. Any phone, anywhere, can open the SOS app from the QR code. No same-Wi-Fi needed.

## 1. Upload to GitHub (5 min)
1. github.com → sign in → **+** → **New repository** → name `resqlink` → **Public** → Create.
2. Click **uploading an existing file**.
3. Unzip `ResQLink_Project.zip`, open the `resqlink` folder, select **everything inside it** (backend, frontend, render.yaml, Dockerfile …) and drag it in. Wait for the upload to finish → **Commit changes**.
   - Check that `render.yaml` is at the top level of the repo, not inside another folder.

## 2. Deploy on Render (10 min)
1. render.com → **Sign in with GitHub**.
2. **New +** → **Blueprint** → pick the `resqlink` repo → **Apply**. (It reads `render.yaml`.)
   - Or: **New +** → **Web Service** → pick the repo →
     Build command `pip install -r backend/requirements.txt` ·
     Start command `uvicorn backend.app:app --host 0.0.0.0 --port $PORT` · Instance type **Free**.
3. Wait for **Live** (first build 3–6 min). Open the link.

## 3. Check (2 min)
- `https://YOUR-LINK/api/health` shows `"ok": true`.
- The 🌐 chip shows **LIVE DATA**.
- The QR code on the command centre now points to the public link. Scan it with a phone on mobile data, then send an SOS. It appears on the map.

## Optional: Google Weather
Render → your service → **Environment** → add `GOOGLE_WEATHER_KEY` = your key → Save (it redeploys). Or paste the key in the app (GOOGLE chip).

## Good to know
- **Free plan sleeps after 15 min idle**, and the first visit then takes ~1 minute. Open the link 5 minutes before you present.
- Village search is ready ~30 s after each start (1.18 M places load in the background). City search works immediately.
- SOS data resets when the free server restarts, which is fine for a demo.
- Other hosts: `Dockerfile` (Railway, Fly.io, Google Cloud Run) and `Procfile` (Heroku-style) are included.
- Backup if the venue internet is down: run `start.bat` on the laptop + phone hotspot, or open `standalone/ResQLink.html`.


# Netlify

Netlify hosts **static pages** (no Python server), so there are two ways:

## A. Quick: static only (2 minutes)
1. Go to **app.netlify.com/drop** and log in.
2. Drag the **`frontend`** folder (or `netlify_site.zip`) onto the page.
3. You get `https://something.netlify.app`. Rename it under *Site configuration → Change site name*.

Works: globe, search (all villages), live weather (Open-Meteo straight from the browser), prediction, All-India 3D, Simple mode, live maps, alerts, what-if, simulated SOS mesh, Google Weather (key saved in the browser).
Not working without the backend: real phone SOS (QR code), rescue screen, server cache, map-tile relay.

## B. Full: Netlify frontend + Render backend
1. Deploy the backend on Render (section above). Note its URL, e.g. `https://resqlink-ab12.onrender.com`.
2. On Render → *Environment* → add `PUBLIC_URL` = your Netlify address (e.g. `https://resqlink.netlify.app`), so the QR code points to Netlify.
3. In `frontend/_redirects`, remove the `# ` before the `/api/*` line and put in your Render URL:
   `/api/*    https://resqlink-ab12.onrender.com/api/:splat    200`
4. Drag the `frontend` folder to Netlify Drop again (or push to GitHub if the site is linked).
5. Open the site. The chip should say **BACKEND ONLINE** and the QR code shows `…netlify.app/sos`.

Git deploy instead of drag-and-drop: *Add new site → Import from GitHub* → pick the repo. `netlify.toml` already says publish `frontend`, no build command.

Tip: Render's free server sleeps after 15 minutes. Open the site once 5 minutes before presenting.
