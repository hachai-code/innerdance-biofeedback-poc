# database/

Supabase Postgres schema. Contains all table definitions, the `feature_dataset` view, and setup instructions.

---

## Setup (one-time)

1. Create a free Supabase project at supabase.com.
2. Open the SQL Editor in Supabase Studio.
3. Paste and run `schema.sql`.
4. Enable the `pgvector` extension (for future semantic search): Dashboard → Database → Extensions → enable `vector`.
5. Create a Storage bucket named `rr-files` (Dashboard → Storage → New bucket, set to private).

---

## Tables

| Table | Purpose |
|---|---|
| `participants` | One row per study participant |
| `sessions` | One row per innerdance session. Links participant ↔ R-R file ↔ form data |
| `hrv_windows` | One row per 5-min pre/post window or 30-sec in-session window |
| `acoustic_windows` | One row per 30-sec audio window |
| `feature_dataset` | SQL VIEW joining hrv + acoustic + session metadata |

---

## Who uses what

| User | Access |
|---|---|
| Participants | Supabase REST API via Streamlit app only |
| Non-experts | Supabase Studio (table editor + SQL console) + Metabase |
| AI engineers | Python via `supabase-py` or `sqlalchemy`. Query `feature_dataset` |
| Facilitators | Supabase REST API via Streamlit dashboard (future) |

---

## Metabase connection

Connect Metabase to Supabase Postgres:
- Host: `db.<project-ref>.supabase.co`
- Port: `5432`
- Database: `postgres`
- Username: `postgres`
- Password: your Supabase database password (Settings → Database)

---

## Adding a new column

Always add to both the table and the `feature_dataset` view. Update `data/README.md` if it is a new self-report field.
