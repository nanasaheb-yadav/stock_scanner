import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse

app = FastAPI(title="Robust Nifty 500 Scanner")

# Simplified symbol list
NIFTY500 = ["RELIANCE.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","TCS.NS" /*… all 500…*/]

# Shared storage for latest scan
latest_scan = {"status": "idle", "timestamp": None, "results": []}

def fetch_weekly(symbol, years=2):
    end = datetime.today()
    start = end - timedelta(days=years*365)
    df = yf.Ticker(symbol).history(start=start, end=end, interval="1wk")
    if len(df) < years*40:
        daily = yf.Ticker(symbol).history(start=start, end=end, interval="1d")
        if daily.empty: return pd.DataFrame()
        weekly = pd.DataFrame({
            'Open': daily['Open'].resample('W-FRI').first(),
            'High': daily['High'].resample('W-FRI').max(),
            'Low': daily['Low'].resample('W-FRI').min(),
            'Close': daily['Close'].resample('W-FRI').last(),
            'Volume': daily['Volume'].resample('W-FRI').sum()
        }).dropna().reset_index()
        return weekly
    return df.reset_index()

def analyze_stock(sym):
    df = fetch_weekly(sym)
    if len(df) < 20: return None
    close = df['Close']
    # HMA
    def hma(series,n):
        half=int(n/2); sq=int(np.sqrt(n))
        w1=series.rolling(half).mean(); w2=series.rolling(n).mean()
        raw=2*w1-w2
        return raw.rolling(sq).mean()
    h30=hma(close,30).iloc[-1]; h44=hma(close,44).iloc[-1]
    # MACD
    e3=close.ewm(span=3).mean(); e21=close.ewm(span=21).mean()
    macd=e3-e21; sig=macd.ewm(span=9).mean(); hist=macd-sig
    # RSI
    d=close.diff(); g=d.clip(lower=0).rolling(9).mean(); l=(-d).clip(lower=0).rolling(9).mean()
    rs=g/l; rsi=100-100/(1+rs)
    s3=rsi.rolling(3).mean()
    w21=rsi.rolling(21).apply(lambda x: np.dot(x,np.arange(1,22))/np.arange(1,22).sum())
    # Count criteria
    crit=0
    crit+=h30>hma(close,30).iloc[-2]
    crit+=h30<=close.iloc[-1]<=h44
    crit+=((hist<0).tail(20).sum()>=8 and macd.iloc[-1]>sig.iloc[-1])
    crit+=(rsi.iloc[-1]>w21.iloc[-1] and s3.iloc[-1]>w21.iloc[-1])
    crit+=1
    if crit<2: return None
    sl=h30*0.95; tgt=close.iloc[-1]*1.15
    rr=(tgt-close.iloc[-1])/(close.iloc[-1]-sl) if close.iloc[-1]>sl else 0
    return {"symbol":sym,"price":round(float(close.iloc[-1]),2),
            "criteria_met":int(crit),"stop_loss":round(sl,2),
            "target":round(tgt,2),"risk_reward":round(rr,2)}

def run_full_scan():
    results=[]
    for sym in NIFTY500:
        res=analyze_stock(sym)
        if res: results.append(res)
    latest_scan.update({"status":"completed","timestamp":datetime.now().isoformat(),"results":results})

@app.get("/health")
def health():
    """Always return 200 OK immediately."""
    return JSONResponse({"status":"ok"})

@app.post("/start-scan")
def start_scan(background_tasks: BackgroundTasks):
    """Trigger scan in background, return immediately."""
    if latest_scan["status"]=="running":
        return JSONResponse({"status":"already_running"}, status_code=202)
    latest_scan.update({"status":"running","results":[]})
    background_tasks.add_task(run_full_scan)
    return JSONResponse({"status":"scan_started"}, status_code=202)

@app.get("/results")
def get_results():
    """Fetch latest scan results."""
    return latest_scan
