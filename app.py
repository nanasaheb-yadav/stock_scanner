# app.py

from nsetools import Nse
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="Full NSE Scanner")

# 1) Dynamically load ALL NSE-listed symbols
nse_client = Nse()
all_codes = nse_client.get_stock_codes()  # Dict: {symbol: name}
# Remove the header entry
all_codes.pop('SYMBOL', None)
# Append “.NS” suffix for Yahoo Finance
NSE_SYMBOLS = [f"{sym}.NS" for sym in all_codes.keys()]

# Shared storage for latest scan
latest_scan = {"status":"idle","timestamp":None,"results":[]}

def fetch_weekly(symbol: str, years: int = 2) -> pd.DataFrame:
    end = datetime.today()
    start = end - timedelta(days=years*365)
    df = yf.Ticker(symbol).history(
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        interval="1wk"
    )
    if len(df) < years*40:
        daily = yf.Ticker(symbol).history(
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval="1d"
        )
        if daily.empty:
            return pd.DataFrame()
        weekly = pd.DataFrame({
            'Open': daily['Open'].resample('W-FRI').first(),
            'High': daily['High'].resample('W-FRI').max(),
            'Low':  daily['Low'].resample('W-FRI').min(),
            'Close':daily['Close'].resample('W-FRI').last(),
            'Volume':daily['Volume'].resample('W-FRI').sum()
        }).dropna().reset_index()
        return weekly
    return df.reset_index()

def calc_hma(series: pd.Series, n: int) -> pd.Series:
    half, sq = int(n/2), int(np.sqrt(n))
    w1 = series.rolling(half).mean()
    w2 = series.rolling(n).mean()
    raw = 2*w1 - w2
    return raw.rolling(sq).mean()

def calc_macd(series: pd.Series):
    e3  = series.ewm(span=3).mean()
    e21 = series.ewm(span=21).mean()
    macd = e3 - e21
    sig  = macd.ewm(span=9).mean()
    hist = macd - sig
    return macd, sig, hist

def calc_rsi(series: pd.Series):
    d = series.diff()
    g = d.clip(lower=0).rolling(9).mean()
    l = (-d).clip(lower=0).rolling(9).mean()
    rs = g/l
    rsi = 100 - 100/(1+rs)
    sma3 = rsi.rolling(3).mean()
    wma21 = rsi.rolling(21).apply(lambda x: np.dot(x, np.arange(1,22))/np.arange(1,22).sum())
    return rsi, sma3, wma21

def analyze_stock(sym: str):
    df = fetch_weekly(sym)
    if len(df) < 20:
        return None
    close = df['Close']
    h30 = calc_hma(close,30).iloc[-1]
    h44 = calc_hma(close,44).iloc[-1]
    macd, sig, hist = calc_macd(close)
    rsi, s3, w21 = calc_rsi(close)
    crit = 0
    crit += int(h30 > calc_hma(close,30).iloc[-2])
    crit += int(h30 <= close.iloc[-1] <= h44)
    crit += int((hist<0).tail(20).sum()>=8 and macd.iloc[-1]>sig.iloc[-1])
    crit += int(rsi.iloc[-1]>w21.iloc[-1] and s3.iloc[-1]>w21.iloc[-1])
    crit += 1
    if crit < 2:
        return None
    sl  = h30 * 0.95
    tgt = close.iloc[-1] * 1.15
    rr  = (tgt-close.iloc[-1])/(close.iloc[-1]-sl) if close.iloc[-1]>sl else 0
    return {
        "symbol": sym,
        "price": round(float(close.iloc[-1]),2),
        "criteria_met": crit,
        "stop_loss": round(sl,2),
        "target": round(tgt,2),
        "risk_reward": round(rr,2)
    }

def run_full_scan():
    latest_scan["status"] = "running"
    results = []
    for sym in NIFTY500:
        res = analyze_stock(sym)
        if res:
            results.append(res)
    latest_scan.update({
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "results": results
    })

@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})

@app.post("/start-scan")
def start_scan(background_tasks: BackgroundTasks):
    if latest_scan["status"] == "running":
        return JSONResponse({"status": "already_running"}, status_code=202)
    background_tasks.add_task(run_full_scan)
    return JSONResponse({"status": "scan_started"}, status_code=202)

@app.get("/results")
def get_results():
    return latest_scan

@app.get("/", response_class=HTMLResponse)
def homepage():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Nifty 500 Scanner</title>
  <style>
    body { font-family: sans-serif; background:#1a1a1a; color:#eee; text-align:center; padding:50px; }
    button { padding:15px 30px; font-size:1.2em; background:#4CAF50; color:#fff; border:none; border-radius:5px; cursor:pointer; }
    button:disabled { background:#555; cursor:not-allowed; }
    #status { margin-top:20px; }
    #results { margin:20px auto; max-width:800px; text-align:left; }
    table { width:100%; border-collapse:collapse; margin-top:10px; }
    th,td { padding:8px; border:1px solid #444; }
    th { background:#333; }
  </style>
</head>
<body>
  <h1>🚀 Nifty 500 Scanner</h1>
  <button id="scanBtn" onclick="startScan()">Start Scan</button>
  <div id="status">Status: idle</div>
  <div id="results"></div>
<script>
async function startScan(){
  document.getElementById('scanBtn').disabled = true;
  document.getElementById('status').textContent = 'Status: running';
  await fetch('/start-scan',{method:'POST'});
  const iv = setInterval(async ()=>{
    const res = await fetch('/results');
    const j = await res.json();
    document.getElementById('status').textContent = 'Status: '+j.status;
    if(j.status==='completed'){
      clearInterval(iv);
      renderResults(j.results);
      document.getElementById('scanBtn').disabled = false;
    }
  },10000);
}
function renderResults(data){
  if(!data.length){
    document.getElementById('results').innerHTML = '<p>No results.</p>';
    return;
  }
  let html = '<table><tr><th>Symbol</th><th>Price</th><th>Criteria</th><th>SL</th><th>Target</th><th>RR</th></tr>';
  data.forEach(r=> html+=
    `<tr><td>${r.symbol}</td><td>${r.price}</td><td>${r.criteria_met}</td>`+
    `<td>${r.stop_loss}</td><td>${r.target}</td><td>${r.risk_reward}</td></tr>`
  );
  html += '</table>';
  document.getElementById('results').innerHTML = html;
}
</script>
</body>
</html>
""")

# To run locally:
# uvicorn app:app --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import os, uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, log_level="info")
