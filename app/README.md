# app/

Streamlit participant upload app (Phase 0 of the data collection platform).

---

## What it does

A simple web form where participants:
1. Enter their participant ID and session date
2. Fill in the self-report form (PSS-3, energy, sleep)
3. Upload their Polar H10 R-R CSV file
4. Paste their Spotify playlist link (or upload audio file)

On submit, the form writes to Supabase: R-R file → Storage bucket, metadata → `sessions` table, form data → `sessions.form_data` (JSONB).

---

## Running locally

```bash
pip install streamlit supabase
streamlit run app/upload_app.py
```

Requires a `.env` file with:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

---

## Deploying to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to share.streamlit.io → New app → select this repo → `app/upload_app.py`.
3. Add the env vars in the Streamlit Secrets panel.
4. Share the URL with participants.

---

## Status

`upload_app.py` is not yet built. The file is a placeholder. See `docs/architecture.md` for the full design and `database/schema.sql` for the Supabase tables it writes to.

---

## Phase roadmap

| Phase | Tool | Status |
|---|---|---|
| 0 (now) | Google Drive + Google Form | Use this until Streamlit app is ready |
| 1 | This Streamlit app | Not yet built |
| 2 | Mobile-friendly Streamlit + audio upload | Future |
| 3 | Polar SDK + live RMSSD | Future |
