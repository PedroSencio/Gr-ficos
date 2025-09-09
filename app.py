from flask import Flask, send_file
import io
from datetime import date, timedelta, datetime, timezone
import os

# Matplotlib "sem tela"
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from supabase import create_client

SUPABASE_URL = "https://frpqytwwgcxudrtenskk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZycHF5dHd3Z2N4dWRydGVuc2trIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwMDQ1NjIsImV4cCI6MjA3MjU4MDU2Mn0.KoqxNqEH_eGkZ6FzykzlUM7PyPv0sXkcrGC6RqxATjY"   # anon (com RLS de SELECT) ou service_role (apenas no backend)
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)

@app.get("/")
def ok():
    return "OK — abra /plot.png"

@app.get("/apolices-15-dias.png")
def plot_png():
    dias = 15
    hoje_utc = datetime.now(timezone.utc).date()
    inicio   = hoje_utc - timedelta(days=dias)
    amanha   = hoje_utc + timedelta(days=1)  # limite exclusivo (< amanhã)

    # Busca apólices criadas na janela
    resp = (
        sb.table("apolices")
          .select("id, created_at")
          .gte("created_at", inicio.isoformat())
          .lt("created_at",  amanha.isoformat())
          .order("created_at")
          .execute()
    )
    rows = resp.data or []

    # Contagem por dia (preenche dias sem dado com 0)
    xs = [inicio + timedelta(days=i) for i in range(dias + 1)]
    counts = {d: 0 for d in xs}
    for r in rows:
        d = date.fromisoformat(r["created_at"][:10])   # pega só YYYY-MM-DD (UTC)
        if d in counts:
            counts[d] += 1
    ys = [counts[d] for d in xs]

    # --- BARRAS ---
    plt.figure(figsize=(8, 3))
    plt.bar(xs, ys, width=0.8, align="center")  # ← barras
    plt.title(f"Apólices criadas (últimos {dias} dias)")
    plt.xlabel("Data (UTC)")
    plt.ylabel("Quantidade")

    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, dias // 10)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    plt.gcf().autofmt_xdate(rotation=30)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=320)
    plt.close()
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
