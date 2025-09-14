# app.py

import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="Full NSE Scanner")

def get_all_nse_symbols():
    """Fetch all NSE symbols from multiple sources"""
    symbols = set()
    
    # Method 1: Get from NSE website directly
    try:
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for stock in data.get('data', []):
                if stock.get('symbol'):
                    symbols.add(f"{stock['symbol']}.NS")
    except:
        pass
    
    # Method 2: Fallback to a comprehensive hardcoded list of major NSE stocks
    major_nse_stocks = [
        # Nifty 50
        "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "TCS.NS",
        "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "ASIANPAINT.NS",
        "MARUTI.NS", "BAJFINANCE.NS", "HCLTECH.NS", "AXISBANK.NS", "LT.NS",
        "NESTLEIND.NS", "KOTAKBANK.NS", "TITAN.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS",
        "WIPRO.NS", "NTPC.NS", "JSWSTEEL.NS", "TATAMOTORS.NS", "POWERGRID.NS",
        "M&M.NS", "TECHM.NS", "ONGC.NS", "TATASTEEL.NS", "DIVISLAB.NS",
        "BAJAJFINSV.NS", "HDFCLIFE.NS", "INDUSINDBK.NS", "ADANIPORTS.NS", "COALINDIA.NS",
        "DRREDDY.NS", "SBILIFE.NS", "GRASIM.NS", "CIPLA.NS", "TATACONSUM.NS",
        "BRITANNIA.NS", "EICHERMOT.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "UPL.NS",
        "HINDALCO.NS", "BPCL.NS", "IOC.NS", "APOLLOHOSP.NS", "PIDILITIND.NS",
        
        # Next 50
        "ABB.NS", "ADANIENT.NS", "ADANIGREEN.NS", "AMBUJACEM.NS", "AUBANK.NS",
        "BANKBARODA.NS", "BERGEPAINT.NS", "BEL.NS", "BIOCON.NS", "BOSCHLTD.NS",
        "CANBK.NS", "CHOLAFIN.NS", "COLPAL.NS", "CONCOR.NS", "DABUR.NS",
        "DLF.NS", "DMART.NS", "FEDERALBNK.NS", "GAIL.NS", "GODREJCP.NS",
        "HAVELLS.NS", "HDFC.NS", "HDFCAMC.NS", "HINDPETRO.NS", "ICICIPRULI.NS",
        "IDEA.NS", "INDIANB.NS", "INDIGO.NS", "INDUSTOWER.NS", "IRB.NS",
        "JUBLFOOD.NS", "LICHSGFIN.NS", "LUPIN.NS", "MARICO.NS", "MGL.NS",
        "MPHASIS.NS", "MRF.NS", "NAUKRI.NS", "NMDC.NS", "OFSS.NS",
        "PAGEIND.NS", "PETRONET.NS", "PEL.NS", "PNB.NS", "PFC.NS",
        "RBLBANK.NS", "SAIL.NS", "SBICARD.NS", "SIEMENS.NS", "SRF.NS",
        
        # Additional major stocks
        "3MINDIA.NS", "ACC.NS", "AIAENG.NS", "APLLTD.NS", "ALKEM.NS",
        "AMARAJABAT.NS", "ASHOKLEY.NS", "ASTRAL.NS", "ATUL.NS", "BAJAJHLDNG.NS",
        "BALKRISIND.NS", "BANDHANBNK.NS", "BATAINDIA.NS", "BHARATFORG.NS", "BHEL.NS",
        "BLUESTARCO.NS", "CEATLTD.NS", "CHAMBLFERT.NS", "CHENNPETRO.NS", "CROMPTON.NS",
        "CUMMINSIND.NS", "DEEPAKNITRITE.NS", "DIXON.NS", "EMAMILTD.NS", "ESCORTS.NS",
        "EXIDEIND.NS", "FORTIS.NS", "GLENMARK.NS", "GNFC.NS", "GRANULES.NS",
        "GUJGASLTD.NS", "HAL.NS", "HINDCOPPER.NS", "HINDZINC.NS", "HONAUT.NS",
        "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS",
        "INDIAMART.NS", "INDUSTOWER.NS", "INOXLEISUR.NS", "IPCALAB.NS", "ISEC.NS",
        "JKCEMENT.NS", "JSWENERGY.NS", "JUSTDIAL.NS", "KAJARIACER.NS", "KANSAINER.NS",
        "KTKBANK.NS", "L&TFH.NS", "LALPATHLAB.NS", "LAURUSLABS.NS", "MANAPPURAM.NS",
        "MINDTREE.NS", "MOTHERSUMI.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", "NCCLTD.NS",
        "NH.NS", "NHPC.NS", "OBEROIRLTY.NS", "OIL.NS", "ORIENTBANK.NS",
        "PFIZER.NS", "PIIND.NS", "POLYCAB.NS", "PRESTIGE.NS", "PNBHOUSING.NS",
        "QUESS.NS", "RADICO.NS", "RAIN.NS", "RAMCOCEM.NS", "RPOWER.NS",
        "SANOFI.NS", "SCHAEFFLER.NS", "SHREECEM.NS", "STARCEMENT.NS", "SUDARSCHEM.NS",
        "SYMPHONY.NS", "THERMAX.NS", "THYROCARE.NS", "TIINDIA.NS", "TORNTPHARM.NS",
        "TORNTPOWER.NS", "TRENT.NS", "TRIDENT.NS", "UCOBANK.NS", "UJJIVAN.NS",
        "UNIONBANK.NS", "UNITECH.NS", "UBL.NS", "VEDL.NS", "VOLTAS.NS",
        "WABAG.NS", "WELCORP.NS", "WHIRLPOOL.NS", "YESBANK.NS", "ZEEL.NS"
    ]
    
    symbols.update(major_nse_stocks)
    
    # Convert to sorted list
    return sorted(list(symbols))

# Get all NSE symbols at startup
NSE_SYMBOLS = get_all_nse_symbols()
print(f"Loaded {len(NSE_SYMBOLS)} NSE symbols")

# Shared storage for latest scan
latest_scan = {"status": "idle", "timestamp": None, "results": []}

def fetch_weekly(symbol: str, years: int = 2) -> pd.DataFrame:
    end = datetime.today()
    start = end - timedelta(days=years*365)
    try:
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
    except:
        return pd.DataFrame()

def calc_hma(series: pd.Series, n: int) -> pd.Series:
    try:
        half, sq = int(n/2), int(np.sqrt(n))
        w1 = series.rolling(half).mean()
        w2 = series.rolling(n).mean()
        raw = 2*w1 - w2
        return raw.rolling(sq).mean()
    except:
        return pd.Series([np.nan] * len(series))

def calc_macd(series: pd.Series):
    try:
        e3  = series.ewm(span=3).mean()
        e21 = series.ewm(span=21).mean()
        macd = e3 - e21
        sig  = macd.ewm(span=9).mean()
        hist = macd - sig
        return macd, sig, hist
    except:
        return pd.Series([np.nan] * len(series)), pd.Series([np.nan] * len(series)), pd.Series([np.nan] * len(series))

def calc_rsi(series: pd.Series):
    try:
        d = series.diff()
        g = d.clip(lower=0).rolling(9).mean()
        l = (-d).clip(lower=0).rolling(9).mean()
        rs = g/l
        rsi = 100 - 100/(1+rs)
        sma3 = rsi.rolling(3).mean()
        wma21 = rsi.rolling(21).apply(lambda x: np.dot(x, np.arange(1,22))/np.arange(1,22).sum() if len(x)==21 else np.nan)
        return rsi, sma3, wma21
    except:
        return pd.Series([np.nan] * len(series)), pd.Series([np.nan] * len(series)), pd.Series([np.nan] * len(series))

def analyze_stock(sym: str):
    try:
        df = fetch_weekly(sym)
        if len(df) < 20:
            return None
        close = df['Close']
        
        h30 = calc_hma(close,30)
        h44 = calc_hma(close,44)
        if pd.isna(h30.iloc[-1]) or pd.isna(h44.iloc[-1]):
            return None
            
        macd, sig, hist = calc_macd(close)
        rsi, s3, w21 = calc_rsi(close)
        
        crit = 0
        # Criterion 1: HMA trend
        if len(h30) >= 2 and not pd.isna(h30.iloc[-2]):
            crit += int(h30.iloc[-1] > h30.iloc[-2])
        
        # Criterion 2: Price position
        if not pd.isna(h30.iloc[-1]) and not pd.isna(h44.iloc[-1]):
            crit += int(h30.iloc[-1] <= close.iloc[-1] <= h44.iloc[-1])
        
        # Criterion 3: MACD setup
        if not pd.isna(macd.iloc[-1]) and not pd.isna(sig.iloc[-1]):
            bars_below = (hist < 0).tail(20).sum()
            crit += int(bars_below >= 8 and macd.iloc[-1] > sig.iloc[-1])
        
        # Criterion 4: RSI crossover
        if not pd.isna(rsi.iloc[-1]) and not pd.isna(s3.iloc[-1]) and not pd.isna(w21.iloc[-1]):
            crit += int(rsi.iloc[-1] > w21.iloc[-1] and s3.iloc[-1] > w21.iloc[-1])
        
        # Criterion 5: Weekly timeframe
        crit += 1
        
        if crit < 2:
            return None
            
        sl  = h30.iloc[-1] * 0.95
        tgt = close.iloc[-1] * 1.15
        rr  = (tgt-close.iloc[-1])/(close.iloc[-1]-sl) if close.iloc[-1]>sl else 0
        
        return {
            "symbol": sym.replace('.NS', ''),
            "price": round(float(close.iloc[-1]),2),
            "criteria_met": crit,
            "stop_loss": round(sl,2),
            "target": round(tgt,2),
            "risk_reward": round(rr,2)
        }
    except Exception as e:
        print(f"Error analyzing {sym}: {e}")
        return None

def run_full_scan():
    latest_scan["status"] = "running"
    results = []
    total = len(NSE_SYMBOLS)
    
    for i, sym in enumerate(NSE_SYMBOLS):
        if i % 50 == 0:  # Progress update every 50 stocks
            print(f"Scanning progress: {i}/{total} ({i/total*100:.1f}%)")
        
        res = analyze_stock(sym)
        if res:
            results.append(res)
    
    latest_scan.update({
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "results": sorted(results, key=lambda x: x['criteria_met'], reverse=True)
    })
    print(f"Scan completed. Found {len(results)} qualified stocks out of {total}")

@app.get("/health")
def health():
    return JSONResponse({"status": "ok", "symbols_loaded": len(NSE_SYMBOLS)})

@app.post("/start-scan")
def start_scan(background_tasks: BackgroundTasks):
    if latest_scan["status"] == "running":
        return JSONResponse({"status": "already_running"}, status_code=202)
    background_tasks.add_task(run_full_scan)
    return JSONResponse({"status": "scan_started", "total_symbols": len(NSE_SYMBOLS)}, status_code=202)

@app.get("/results")
def get_results():
    return latest_scan

@app.get("/", response_class=HTMLResponse)
def homepage():
    return HTMLResponse(f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Full NSE Scanner</title>
  <style>
    body {{ font-family: sans-serif; background:#1a1a1a; color:#eee; text-align:center; padding:50px; }}
    button {{ padding:15px 30px; font-size:1.2em; background:#4CAF50; color:#fff; border:none; border-radius:5px; cursor:pointer; }}
    button:disabled {{ background:#555; cursor:not-allowed; }}
    #status {{ margin-top:20px; }}
    #results {{ margin:20px auto; max-width:1000px; text-align:left; }}
    table {{ width:100%; border-collapse:collapse; margin-top:10px; }}
    th,td {{ padding:8px; border:1px solid #444; }}
    th {{ background:#333; }}
    .criteria-5 {{ background:#4CAF50; color:white; }}
    .criteria-4 {{ background:#8BC34A; color:white; }}
    .criteria-3 {{ background:#FF9800; color:white; }}
    .criteria-2 {{ background:#FF5722; color:white; }}
  </style>
</head>
<body>
  <h1>🚀 Full NSE Scanner ({len(NSE_SYMBOLS)} Stocks)</h1>
  <p>Scanning entire NSE universe with 2+ criteria qualification</p>
  <button id="scanBtn" onclick="startScan()">Start Full NSE Scan</button>
  <div id="status">Status: idle</div>
  <div id="results"></div>
<script>
async function startScan(){{
  document.getElementById('scanBtn').disabled = true;
  document.getElementById('status').textContent = 'Status: running (this may take 10-20 minutes)';
  await fetch('/start-scan',{{method:'POST'}});
  const iv = setInterval(async ()=>{{
    const res = await fetch('/results');
    const j = await res.json();
    document.getElementById('status').textContent = 'Status: '+j.status;
    if(j.status==='completed'){{
      clearInterval(iv);
      renderResults(j.results);
      document.getElementById('scanBtn').disabled = false;
    }}
  }},15000);
}}
function renderResults(data){{
  if(!data.length){{
    document.getElementById('results').innerHTML = '<p>No results found.</p>';
    return;
  }}
  let html = '<h2>Qualified Stocks (' + data.length + ' found)</h2>';
  html += '<table><tr><th>Symbol</th><th>Price</th><th>Criteria</th><th>Stop Loss</th><th>Target</th><th>Risk:Reward</th></tr>';
  data.forEach(r=> {{
    const criteriaClass = 'criteria-' + r.criteria_met;
    html += `<tr><td>${{r.symbol}}</td><td>₹${{r.price}}</td>`;
    html += `<td><span class="${{criteriaClass}}">${{r.criteria_met}}/5</span></td>`;
    html += `<td>₹${{r.stop_loss}}</td><td>₹${{r.target}}</td><td>${{r.risk_reward}}</td></tr>`;
  }});
  html += '</table>';
  document.getElementById('results').innerHTML = html;
}}
</script>
</body>
</html>
""")

if __name__ == "__main__":
    import os, uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, log_level="info")
