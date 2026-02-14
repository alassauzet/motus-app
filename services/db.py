import os
from supabase import create_client

# Utilise les clés d'environnement
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_ANON_KEY"]  # ou SUPABASE_SERVICE_ROLE_KEY si besoin de droits admin

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
