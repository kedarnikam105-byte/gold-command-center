# Trading Signal App (BTC & Gold)

Free-tier trading signal system with:
- Python agents that generate signals
- Supabase as database
- GitHub Actions as scheduler
- Streamlit app with 3 views: Trader, Team Lead, Agent Monitor

## Setup
1. Create Supabase project -> run `supabase/schema.sql`
2. Copy Supabase URL + keys
3. Add GitHub secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
4. Enable GitHub Actions (runs every 15 min)
5. Deploy `app.py` on Streamlit Cloud
6. Add secrets in Streamlit Cloud: `SUPABASE_URL`, `SUPABASE_ANON_KEY`
