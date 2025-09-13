import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Robust Nifty 500 Scanner")

# 1) Full Nifty 500 symbol list (abbreviated here—you can expand as needed)
NIFTY500 = [
    "RELIANCE.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","TCS.NS",
    # … include all 500 symbols …
]

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
        }).dropna()
        weekly.reset_index(inplace=True)
        return weekly
    df.reset_index(inplace=True)
    return df

def calc_hma(series, n):
    half = int(n/2); sq = int(np.sqrt(n))
    wma1 = series.rolling(half).apply(lambda x: np.dot(x, np.arange(1,len(x)+1))/np.arange(1,len(x)+1).sum())
    wma2 = series.rolling(n).apply(lambda x: np.dot(x, np.arange(1,len(x)+1))/np.arange(1,len(x)+1).sum())
    raw = 2*wma1 - wma2
    hma = raw.rolling(sq).apply(lambda x: np.dot(x, np.arange(1,len(x)+1))/np.arange(1,len(x)+1).sum())
    return hma

def calc_macd(series):
    e3 = series.ewm(span=3).mean()
    e21 = series.ewm(span=21).mean()
    macd = e3 - e21
    sig  = macd.ewm(span=9).mean()
    hist = macd - sig
    return macd, sig, hist

def calc_rsi(series):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(9).mean()
    loss = (-delta).clip(lower=0).rolling(9).mean()
    rs = gain/loss
    rsi = 100-100/(1+rs)
    sma3 = rsi.rolling(3).mean()
    wma21 = rsi.rolling(21).apply(lambda x: np.dot(x,np.arange(1,22))/np.arange(1,22).sum())
    return rsi, sma3, wma21

@app.get("/scan")
def scan():
    results=[]
    for sym in NIFTY500:
        df = fetch_weekly(sym)
        if len(df)<20: continue
        close=df['Close']
        h30=calc_hma(close,30).iloc[-1]
        h44=calc_hma(close,44).iloc[-1]
        macd, sig, hist = calc_macd(close)
        rsi, sma3, wma21 = calc_rsi(close)
        crit=0
        crit += h30>calc_hma(close,30).iloc[-2]
        crit += (h30<=close.iloc[-1]<=h44)
        crit += ((hist<0).tail(20).sum()>=8 and macd.iloc[-1]>sig.iloc[-1])
        crit += (rsi.iloc[-1]>wma21.iloc[-1] and sma3.iloc[-1]>wma21.iloc[-1])
        crit += 1
        if crit<2: continue
        sl = h30*0.95
        tgt=close.iloc[-1]*1.15
        rr=(tgt-close.iloc[-1])/(close.iloc[-1]-sl) if close.iloc[-1]>sl else 0
        results.append({
            "symbol":sym,
            "price":round(close.iloc[-1],2),
            "criteria_met":int(crit),
            "stop_loss":round(sl,2),
            "target":round(tgt,2),
            "risk_reward":round(rr,2)
        })
    return JSONResponse({"count":len(results),"results":results})

