import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
import time
import warnings
warnings.filterwarnings('ignore')

app = FastAPI(title="Stock Scanner Pro")

# Configuration - Made more lenient
CONFIG = {
    'min_market_cap_cr': 1,  # Very low threshold - 1 cr
    'fundamental_score_threshold': 3,  # Lower threshold
    'technical_score_threshold': 30,  # Lower threshold
    'request_delay': 0.1  # Delay between requests
}

# Global storage
scan_data = {
    "status": "idle",
    "stage": "ready",
    "progress": 0,
    "total_stocks": 0,
    "fundamental_passed": 0,
    "technical_qualified": 0,
    "fundamental_results": [],
    "final_results": [],
    "last_update": None,
    "debug_info": []
}

# Enhanced NSE Stock Universe
def get_nse_symbols():
    """Get NSE symbols with comprehensive fallback"""
    symbols = set()
    
    # Try NSE API first
    try:
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            for stock in data.get('data', []):
                if stock.get('symbol'):
                    symbols.add(f"{stock['symbol']}.NS")
        print(f"Fetched {len(symbols)} from NSE API")
    except Exception as e:
        print(f"NSE API failed: {e}")
    
    # Comprehensive fallback list - Most liquid NSE stocks
    fallback_stocks = [
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
        
        # Next 50 most liquid
        "ABB.NS", "ADANIENT.NS", "ADANIGREEN.NS", "AMBUJACEM.NS", "AUBANK.NS",
        "BANKBARODA.NS", "BERGEPAINT.NS", "BEL.NS", "BIOCON.NS", "BOSCHLTD.NS",
        "CANBK.NS", "CHOLAFIN.NS", "COLPAL.NS", "CONCOR.NS", "DABUR.NS",
        "DLF.NS", "DMART.NS", "FEDERALBNK.NS", "GAIL.NS", "GODREJCP.NS",
        "HAVELLS.NS", "HDFC.NS", "HDFCAMC.NS", "HINDPETRO.NS", "ICICIPRULI.NS",
        "IDEA.NS", "INDIANB.NS", "INDIGO.NS", "INDUSTOWER.NS", "IRB.NS",
        "JUBLFOOD.NS", "LICHSGFIN.NS", "LUPIN.NS", "MARICO.NS", "MGL.NS",
        "MPHASIS.NS", "MRF.NS", "NAUKRI.NS", "NMDC.NS", "OFSS.NS",
        "PAGEIND.NS", "PETRONET.NS", "PEL.NS", "PNB.NS", "PFC.NS",
        "RBLBANK.NS", "SAIL.NS", "SBICARD.NS", "SIEMENS.NS", "SRF.NS"
    ]
    
    symbols.update(fallback_stocks)
    final_list = sorted(list(symbols))
    print(f"Total symbols loaded: {len(final_list)}")
    return final_list

# Robust Fundamental Data Fetcher
def get_fundamental_data_robust(symbol):
    """Super robust fundamental data fetching with multiple attempts"""
    try:
        print(f"🔍 Fetching fundamental data for {symbol}")
        
        # Add delay to avoid rate limiting
        time.sleep(CONFIG['request_delay'])
        
        # Create ticker with timeout
        ticker = yf.Ticker(symbol)
        
        # Try multiple data sources
        info = None
        
        # Method 1: Regular info
        try:
            info = ticker.info
        except Exception as e1:
            print(f"Method 1 failed for {symbol}: {e1}")
            
            # Method 2: Fast info
            try:
                info = ticker.fast_info
            except Exception as e2:
                print(f"Method 2 failed for {symbol}: {e2}")
                
                # Method 3: Get basic data from history
                try:
                    history = ticker.history(period="5d")
                    if not history.empty:
                        current_price = history['Close'].iloc[-1]
                        info = {'currentPrice': current_price, 'symbol': symbol.replace('.NS', '')}
                except Exception as e3:
                    print(f"Method 3 failed for {symbol}: {e3}")
                    return None
        
        if not info:
            print(f"❌ No info data for {symbol}")
            return None
        
        # Debug: Print available keys
        print(f"📊 Available data keys for {symbol}: {list(info.keys())[:10]}...")
        
        # Extract data with extensive fallbacks
        def safe_extract(key, default=0, multiplier=1):
            """Safely extract data with multiple fallback attempts"""
            try:
                # Try direct access
                if key in info and info[key] is not None:
                    value = info[key]
                    if isinstance(value, (int, float)) and not pd.isna(value):
                        return float(value) * multiplier
                
                # Try alternative keys
                alt_keys = {
                    'currentPrice': ['regularMarketPrice', 'price', 'previousClose'],
                    'marketCap': ['marketCapitalization', 'sharesOutstanding'],
                    'trailingPE': ['pe', 'priceToEarningsRatio', 'peRatio'],
                    'priceToBook': ['pb', 'pbRatio', 'bookValue'],
                    'returnOnEquity': ['roe', 'returnsOnEquity'],
                    'returnOnAssets': ['roa', 'returnsOnAssets'],
                    'profitMargins': ['profitMargin', 'netProfitMargin'],
                    'debtToEquity': ['debtEquityRatio', 'totalDebtToEquity'],
                    'currentRatio': ['currentRatio', 'liquidityRatio']
                }
                
                if key in alt_keys:
                    for alt_key in alt_keys[key]:
                        if alt_key in info and info[alt_key] is not None:
                            try:
                                return float(info[alt_key]) * multiplier
                            except:
                                continue
                
                return default
            except:
                return default
        
        # Calculate market cap if not directly available
        market_cap = safe_extract('marketCap')
        if market_cap == 0:
            shares = safe_extract('sharesOutstanding')
            price = safe_extract('currentPrice')
            if shares > 0 and price > 0:
                market_cap = shares * price
        
        # Minimum market cap check (very lenient)
        min_cap = CONFIG['min_market_cap_cr'] * 10000000  # 1 cr = 10 million
        if market_cap < min_cap and market_cap > 0:
            print(f"⚠️ {symbol} market cap {market_cap/10000000:.1f} cr below threshold")
            return None
        
        # Build comprehensive data dict
        fundamental_data = {
            'symbol': symbol.replace('.NS', ''),
            'company_name': info.get('longName', info.get('shortName', symbol.replace('.NS', ''))),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'market_cap_cr': round(market_cap / 10000000, 2) if market_cap > 0 else 0,
            'current_price': safe_extract('currentPrice'),
            
            # Valuation metrics
            'pe_ratio': safe_extract('trailingPE'),
            'forward_pe': safe_extract('forwardPE'),
            'pb_ratio': safe_extract('priceToBook'),
            'price_to_sales': safe_extract('priceToSalesTrailing12Months'),
            'ev_to_ebitda': safe_extract('enterpriseToEbitda'),
            
            # Profitability metrics
            'roe': safe_extract('returnOnEquity', multiplier=100),
            'roa': safe_extract('returnOnAssets', multiplier=100),
            'profit_margin': safe_extract('profitMargins', multiplier=100),
            'operating_margin': safe_extract('operatingMargins', multiplier=100),
            'gross_margin': safe_extract('grossMargins', multiplier=100),
            
            # Financial health
            'debt_to_equity': safe_extract('debtToEquity'),
            'current_ratio': safe_extract('currentRatio'),
            'quick_ratio': safe_extract('quickRatio'),
            'interest_coverage': safe_extract('interestCoverage'),
            
            # Growth metrics
            'revenue_growth': safe_extract('revenueGrowth', multiplier=100),
            'earnings_growth': safe_extract('earningsGrowth', multiplier=100),
            
            # Dividend info
            'dividend_yield': safe_extract('dividendYield', multiplier=100),
            'payout_ratio': safe_extract('payoutRatio', multiplier=100),
            
            # Other metrics
            'beta': safe_extract('beta', default=1.0),
            'eps': safe_extract('trailingEps'),
            'book_value': safe_extract('bookValue'),
            '52_week_high': safe_extract('fiftyTwoWeekHigh'),
            '52_week_low': safe_extract('fiftyTwoWeekLow'),
            
            # Data quality indicators
            'data_completeness': sum(1 for v in [
                safe_extract('currentPrice'), safe_extract('trailingPE'), safe_extract('returnOnEquity')
            ] if v != 0) / 3
        }
        
        print(f"✅ Successfully extracted data for {symbol}")
        return fundamental_data
        
    except Exception as e:
        print(f"❌ Error fetching fundamentals for {symbol}: {e}")
        return None

# Simplified but Accurate Fundamental Scoring
def calculate_fundamental_score_robust(data):
    """Simplified but robust fundamental scoring"""
    if not data or data.get('data_completeness', 0) < 0.3:
        return {'score': 0, 'grade': 'F', 'passed': False, 'reason': 'Insufficient data'}
    
    try:
        score = 0
        max_score = 10
        score_details = {}
        
        # 1. Price Reasonableness (0-2.5 points)
        pe = data.get('pe_ratio', 0)
        if pe > 0:
            if pe < 10:
                price_score = 2.5
            elif pe < 15:
                price_score = 2.0
            elif pe < 20:
                price_score = 1.5
            elif pe < 30:
                price_score = 1.0
            elif pe < 50:
                price_score = 0.5
            else:
                price_score = 0
        else:
            price_score = 1.0  # Neutral for missing data
        
        score += price_score
        score_details['price_valuation'] = price_score
        
        # 2. Profitability (0-2.5 points) 
        roe = data.get('roe', 0)
        if roe > 0:
            if roe > 20:
                prof_score = 2.5
            elif roe > 15:
                prof_score = 2.0
            elif roe > 12:
                prof_score = 1.5
            elif roe > 8:
                prof_score = 1.0
            elif roe > 5:
                prof_score = 0.5
            else:
                prof_score = 0
        else:
            prof_score = 0
        
        score += prof_score
        score_details['profitability'] = prof_score
        
        # 3. Financial Health (0-2 points)
        debt_equity = data.get('debt_to_equity', 0)
        current_ratio = data.get('current_ratio', 0)
        
        health_score = 0
        if debt_equity > 0:
            if debt_equity < 0.5:
                health_score += 1.0
            elif debt_equity < 1.0:
                health_score += 0.7
            elif debt_equity < 2.0:
                health_score += 0.3
        else:
            health_score += 0.5  # Neutral for missing data
            
        if current_ratio > 1.5:
            health_score += 1.0
        elif current_ratio > 1.0:
            health_score += 0.7
        elif current_ratio > 0.8:
            health_score += 0.3
        else:
            health_score += 0.1
            
        score += min(health_score, 2.0)
        score_details['financial_health'] = min(health_score, 2.0)
        
        # 4. Growth (0-2 points)
        rev_growth = data.get('revenue_growth', 0)
        earnings_growth = data.get('earnings_growth', 0)
        
        growth_score = 0
        if rev_growth > 15:
            growth_score += 1.0
        elif rev_growth > 10:
            growth_score += 0.7
        elif rev_growth > 5:
            growth_score += 0.4
        elif rev_growth > 0:
            growth_score += 0.2
            
        if earnings_growth > 15:
            growth_score += 1.0
        elif earnings_growth > 10:
            growth_score += 0.7
        elif earnings_growth > 5:
            growth_score += 0.4
        elif earnings_growth > 0:
            growth_score += 0.2
            
        score += min(growth_score, 2.0)
        score_details['growth'] = min(growth_score, 2.0)
        
        # 5. Market Presence (0-1 point) - Based on market cap
        market_cap = data.get('market_cap_cr', 0)
        if market_cap > 10000:  # > 10,000 cr
            presence_score = 1.0
        elif market_cap > 1000:  # > 1,000 cr
            presence_score = 0.8
        elif market_cap > 100:   # > 100 cr
            presence_score = 0.6
        elif market_cap > 10:    # > 10 cr
            presence_score = 0.4
        else:
            presence_score = 0.2
            
        score += presence_score
        score_details['market_presence'] = presence_score
        
        # Final score calculation
        final_score = min(score, max_score)
        
        # Grade assignment
        if final_score >= 8.0:
            grade = 'A+'
        elif final_score >= 7.0:
            grade = 'A'
        elif final_score >= 6.0:
            grade = 'B+'
        elif final_score >= 5.0:
            grade = 'B'
        elif final_score >= 4.0:
            grade = 'C+'
        elif final_score >= 3.0:
            grade = 'C'
        else:
            grade = 'D'
        
        return {
            'score': round(final_score, 1),
            'grade': grade,
            'passed': final_score >= CONFIG['fundamental_score_threshold'],
            'score_details': score_details,
            'reason': f"Score: {final_score:.1f}/10"
        }
        
    except Exception as e:
        print(f"Error calculating fundamental score: {e}")
        return {'score': 0, 'grade': 'F', 'passed': False, 'reason': f'Calculation error: {e}'}

# Robust Technical Analysis
def calculate_technical_score_robust(symbol):
    """Robust technical analysis with better error handling"""
    try:
        print(f"🔍 Technical analysis for {symbol}")
        
        ticker = yf.Ticker(symbol)
        
        # Try different periods if 6mo fails
        for period in ["6mo", "3mo", "1mo"]:
            try:
                data = ticker.history(period=period, interval="1d")
                if not data.empty and len(data) >= 20:
                    break
            except:
                continue
        else:
            print(f"❌ No technical data for {symbol}")
            return None
        
        close = data['Close']
        volume = data['Volume']
        high = data['High']
        low = data['Low']
        
        # Calculate indicators with error handling
        try:
            # Moving averages
            sma_10 = close.rolling(10).mean()
            sma_20 = close.rolling(20).mean() if len(close) >= 20 else sma_10
            
            # RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_price = close.iloc[-1]
            current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
            
            # Technical scoring
            tech_score = 0
            
            # Trend Score (0-40)
            if not pd.isna(sma_10.iloc[-1]) and current_price > sma_10.iloc[-1]:
                tech_score += 20
            if len(close) >= 20 and not pd.isna(sma_20.iloc[-1]) and current_price > sma_20.iloc[-1]:
                tech_score += 20
            
            # RSI Score (0-30)
            if 30 <= current_rsi <= 70:
                tech_score += 30
            elif 25 <= current_rsi < 30 or 70 < current_rsi <= 75:
                tech_score += 20
            elif current_rsi < 25 or current_rsi > 75:
                tech_score += 10
            
            # Volume Score (0-20)
            if len(volume) >= 10:
                avg_volume = volume.rolling(10).mean().iloc[-1]
                if volume.iloc[-1] > avg_volume:
                    tech_score += 20
                else:
                    tech_score += 10
            else:
                tech_score += 15
            
            # Price Position Score (0-10)
            if len(close) >= 50:
                high_period = high.rolling(50).max().iloc[-1]
                low_period = low.rolling(50).min().iloc[-1]
                if high_period != low_period:
                    price_pos = (current_price - low_period) / (high_period - low_period) * 100
                    if 40 <= price_pos <= 80:
                        tech_score += 10
                    elif 20 <= price_pos < 40 or 80 < price_pos <= 90:
                        tech_score += 7
                    else:
                        tech_score += 5
                else:
                    tech_score += 5
            else:
                tech_score += 5
            
            # Determine recommendation
            if tech_score >= 80:
                recommendation = 'STRONG_BUY'
            elif tech_score >= 65:
                recommendation = 'BUY'
            elif tech_score >= 45:
                recommendation = 'HOLD'
            elif tech_score >= 30:
                recommendation = 'WEAK_HOLD'
            else:
                recommendation = 'AVOID'
            
            print(f"✅ Technical analysis complete for {symbol}: {tech_score}")
            
            return {
                'symbol': symbol.replace('.NS', ''),
                'technical_score': tech_score,
                'recommendation': recommendation,
                'current_price': round(float(current_price), 2),
                'rsi': round(current_rsi, 1),
                'qualified': tech_score >= CONFIG['technical_score_threshold']
            }
            
        except Exception as e:
            print(f"❌ Technical calculation error for {symbol}: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Technical analysis error for {symbol}: {e}")
        return None

# Enhanced Scanning Function
def run_complete_scan():
    """Enhanced scanning with better debugging and error handling"""
    global scan_data
    
    scan_data['status'] = 'running'
    scan_data['stage'] = 'fundamental_filtering'
    scan_data['progress'] = 0
    scan_data['debug_info'] = []
    
    try:
        # Get symbols
        all_symbols = get_nse_symbols()
        scan_data['total_stocks'] = len(all_symbols)
        scan_data['debug_info'].append(f"Starting scan of {len(all_symbols)} stocks")
        
        # Stage 1: Fundamental filtering (scan first 50 stocks for performance)
        fundamental_stocks = []
        scan_limit = min(50, len(all_symbols))  # Limit for performance
        
        for i, symbol in enumerate(all_symbols[:scan_limit]):
            try:
                scan_data['progress'] = int((i / scan_limit) * 50)
                print(f"\n🔄 Processing {i+1}/{scan_limit}: {symbol}")
                
                # Get fundamental data
                fund_data = get_fundamental_data_robust(symbol)
                if fund_data:
                    fund_score = calculate_fundamental_score_robust(fund_data)
                    combined = {**fund_data, **fund_score}
                    
                    if fund_score.get('passed', False):
                        fundamental_stocks.append(combined)
                        scan_data['debug_info'].append(f"✅ {symbol} passed fundamental filter")
                        print(f"✅ {symbol} PASSED fundamental: {fund_score['score']}/10")
                    else:
                        scan_data['debug_info'].append(f"❌ {symbol} failed fundamental: {fund_score.get('reason', 'Unknown')}")
                        print(f"❌ {symbol} failed fundamental: {fund_score.get('reason', 'Low score')}")
                else:
                    scan_data['debug_info'].append(f"❌ {symbol} no fundamental data")
                    print(f"❌ {symbol} no fundamental data available")
                
            except Exception as e:
                error_msg = f"Error processing {symbol}: {e}"
                scan_data['debug_info'].append(error_msg)
                print(f"❌ {error_msg}")
                continue
        
        scan_data['fundamental_passed'] = len(fundamental_stocks)
        scan_data['fundamental_results'] = fundamental_stocks
        scan_data['debug_info'].append(f"Stage 1 complete: {len(fundamental_stocks)} stocks passed fundamental filter")
        
        # Stage 2: Technical analysis
        scan_data['stage'] = 'technical_analysis'
        final_stocks = []
        
        if fundamental_stocks:
            for i, fund_stock in enumerate(fundamental_stocks):
                try:
                    scan_data['progress'] = 50 + int((i / len(fundamental_stocks)) * 50)
                    
                    symbol = f"{fund_stock['symbol']}.NS"
                    print(f"\n🔄 Technical analysis {i+1}/{len(fundamental_stocks)}: {symbol}")
                    
                    tech_result = calculate_technical_score_robust(symbol)
                    
                    if tech_result and tech_result.get('qualified', False):
                        combined = {
                            **fund_stock,
                            **tech_result,
                            'final_score': round((fund_stock['score'] * 10 + tech_result['technical_score']) / 2, 1)
                        }
                        final_stocks.append(combined)
                        scan_data['debug_info'].append(f"✅ {symbol} passed both filters")
                        print(f"✅ {symbol} PASSED both filters")
                    else:
                        tech_score = tech_result.get('technical_score', 0) if tech_result else 0
                        scan_data['debug_info'].append(f"❌ {symbol} failed technical filter: {tech_score}")
                        print(f"❌ {symbol} failed technical: {tech_score}")
                        
                except Exception as e:
                    error_msg = f"Technical analysis error for {fund_stock['symbol']}: {e}"
                    scan_data['debug_info'].append(error_msg)
                    print(f"❌ {error_msg}")
                    continue
        
        # Sort by final score
        final_stocks.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        scan_data['technical_qualified'] = len(final_stocks)
        scan_data['final_results'] = final_stocks
        scan_data['status'] = 'completed'
        scan_data['stage'] = 'completed'
        scan_data['progress'] = 100
        scan_data['last_update'] = datetime.now().isoformat()
        scan_data['debug_info'].append(f"Scan complete: {len(final_stocks)} stocks qualified both filters")
        
        print(f"\n🎉 SCAN COMPLETE!")
        print(f"📊 Total scanned: {scan_limit}")
        print(f"✅ Fundamental passed: {len(fundamental_stocks)}")
        print(f"🎯 Final qualified: {len(final_stocks)}")
        
    except Exception as e:
        error_msg = f"Scan error: {e}"
        scan_data['debug_info'].append(error_msg)
        scan_data['status'] = 'error'
        print(f"❌ {error_msg}")

# API Endpoints
@app.get("/health")
def health():
    return JSONResponse({"status": "ok", "version": "4.0 ROBUST"})

@app.post("/start-scan")
def start_scan(background_tasks: BackgroundTasks):
    if scan_data["status"] == "running":
        return JSONResponse({"status": "already_running"}, status_code=202)
    
    # Reset data
    scan_data.update({
        "status": "idle",
        "stage": "ready", 
        "progress": 0,
        "fundamental_passed": 0,
        "technical_qualified": 0,
        "fundamental_results": [],
        "final_results": [],
        "debug_info": []
    })
    
    background_tasks.add_task(run_complete_scan)
    return JSONResponse({"status": "scan_started"}, status_code=202)

@app.get("/scan-status")
def get_scan_status():
    return JSONResponse(scan_data)

@app.get("/debug")
def get_debug_info():
    return JSONResponse({"debug_info": scan_data.get('debug_info', [])})

@app.get("/results")
def get_results():
    return JSONResponse({
        "fundamental_results": scan_data.get('fundamental_results', []),
        "final_results": scan_data.get('final_results', [])
    })

@app.get("/analyze/{symbol}")
def analyze_stock(symbol: str):
    """ROBUST individual stock analysis"""
    try:
        if not symbol.endswith('.NS'):
            symbol += '.NS'
        
        print(f"\n🔍 ANALYZING {symbol}")
        
        # Get fundamental data
        fund_data = get_fundamental_data_robust(symbol)
        if not fund_data:
            return JSONResponse({
                "error": f"Could not fetch fundamental data for {symbol}. This might be due to: 1) Invalid symbol, 2) Data source issues, 3) Very small market cap. Try symbols like RELIANCE, TCS, HDFCBANK."
            }, status_code=404)
        
        # Calculate scores
        fund_score = calculate_fundamental_score_robust(fund_data)
        tech_result = calculate_technical_score_robust(symbol)
        
        # Combine results
        result = {**fund_data, **fund_score}
        if tech_result:
            result.update(tech_result)
            result['final_score'] = round((fund_score['score'] * 10 + tech_result['technical_score']) / 2, 1)
        else:
            result['technical_score'] = 0
            result['rsi'] = 0
            result['recommendation'] = 'NO_TECHNICAL_DATA'
            result['final_score'] = fund_score['score'] * 10
        
        print(f"✅ Analysis complete for {symbol}")
        return JSONResponse(result)
        
    except Exception as e:
        return JSONResponse({
            "error": f"Analysis failed for {symbol}: {str(e)}. Please try a different symbol or check if the stock is listed on NSE."
        }, status_code=500)

@app.get("/", response_class=HTMLResponse)
def homepage():
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Stock Scanner Pro - ROBUST</title>
    <style>
        :root {
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --success: #059669;
            --warning: #d97706;
            --danger: #dc2626;
            --info: #0891b2;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-400: #9ca3af;
            --gray-500: #6b7280;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--gray-50);
            color: var(--gray-900);
            line-height: 1.6;
        }

        .container { max-width: 1200px; margin: 0 auto; padding: 0 1rem; }

        /* Header */
        .header {
            background: white;
            border-bottom: 1px solid var(--gray-200);
            padding: 2rem 0;
            margin-bottom: 2rem;
        }

        .header h1 {
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--gray-900);
            margin-bottom: 0.5rem;
            letter-spacing: -0.025em;
        }

        .header .subtitle {
            color: var(--gray-600);
            font-size: 1.125rem;
            margin-bottom: 0.25rem;
        }

        .header .description {
            color: var(--gray-500);
            font-size: 0.975rem;
        }

        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.025em;
            background-color: var(--success);
            color: white;
            margin-top: 0.5rem;
        }

        /* Controls */
        .controls {
            display: flex;
            gap: 0.75rem;
            justify-content: center;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.75rem 1.5rem;
            border: 1px solid transparent;
            border-radius: 0.5rem;
            font-size: 0.875rem;
            font-weight: 500;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.15s ease;
            outline: none;
            min-height: 2.5rem;
        }

        .btn:focus {
            outline: 2px solid var(--primary);
            outline-offset: 2px;
        }

        .btn-primary {
            background-color: var(--primary);
            color: white;
            border-color: var(--primary);
            box-shadow: var(--shadow-sm);
        }

        .btn-primary:hover:not(:disabled) {
            background-color: var(--primary-hover);
            border-color: var(--primary-hover);
        }

        .btn-secondary {
            background-color: white;
            color: var(--gray-700);
            border-color: var(--gray-300);
            box-shadow: var(--shadow-sm);
        }

        .btn-secondary:hover:not(:disabled) {
            background-color: var(--gray-50);
            color: var(--gray-900);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        /* Cards */
        .card {
            background: white;
            border: 1px solid var(--gray-200);
            border-radius: 0.75rem;
            box-shadow: var(--shadow-sm);
        }

        /* Progress Section */
        .progress-section {
            padding: 1.5rem;
            margin-bottom: 2rem;
        }

        .stage-text {
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--gray-900);
            margin-bottom: 1rem;
            text-align: center;
        }

        .progress-bar {
            width: 100%;
            height: 0.5rem;
            background-color: var(--gray-200);
            border-radius: 0.25rem;
            overflow: hidden;
            margin-bottom: 0.75rem;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--info));
            transition: width 0.3s ease;
            border-radius: 0.25rem;
        }

        .progress-text {
            font-size: 0.875rem;
            color: var(--gray-600);
            text-align: center;
        }

        /* Stats Grid */
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            padding: 1.25rem;
            text-align: center;
        }

        .stat-number {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 0.5rem;
        }

        .stat-label {
            font-size: 0.875rem;
            color: var(--gray-600);
            font-weight: 500;
        }

        /* Results Section */
        .results {
            padding: 0;
            margin-bottom: 2rem;
        }

        .tabs {
            display: flex;
            border-bottom: 1px solid var(--gray-200);
            background: var(--gray-50);
            border-radius: 0.75rem 0.75rem 0 0;
        }

        .tab {
            flex: 1;
            padding: 1rem 1.25rem;
            text-align: center;
            cursor: pointer;
            font-weight: 500;
            color: var(--gray-600);
            border-bottom: 2px solid transparent;
            transition: all 0.15s ease;
        }

        .tab:first-child { border-radius: 0.75rem 0 0 0; }
        .tab:last-child { border-radius: 0 0.75rem 0 0; }

        .tab.active {
            color: var(--primary);
            border-bottom-color: var(--primary);
            background: white;
        }

        .tab-content {
            display: none;
            padding: 1.5rem;
        }

        .tab-content.active {
            display: block;
        }

        .tab-content h2 {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--gray-900);
            margin-bottom: 1rem;
        }

        /* Tables */
        .table-container {
            overflow-x: auto;
            margin-top: 1rem;
            border-radius: 0.5rem;
            border: 1px solid var(--gray-200);
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--gray-200);
        }

        th {
            background-color: var(--gray-50);
            font-weight: 600;
            font-size: 0.875rem;
            color: var(--gray-700);
        }

        tr:hover {
            background-color: var(--gray-50);
        }

        tr:last-child td {
            border-bottom: none;
        }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }

        .badge-success { background-color: #dcfce7; color: var(--success); }
        .badge-info { background-color: #e0f2fe; color: var(--info); }
        .badge-warning { background-color: #fef3c7; color: var(--warning); }
        .badge-danger { background-color: #fee2e2; color: var(--danger); }
        .badge-secondary { background-color: var(--gray-100); color: var(--gray-600); }

        /* Company Info */
        .company-info {
            display: flex;
            flex-direction: column;
        }

        .company-name {
            font-weight: 600;
            color: var(--gray-900);
            margin-bottom: 0.125rem;
        }

        .company-sector {
            color: var(--gray-500);
            font-size: 0.8125rem;
        }

        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 3rem 1.5rem;
            color: var(--gray-500);
        }

        .empty-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }

        /* Loading */
        .loading {
            text-align: center;
            padding: 3rem;
            color: var(--gray-500);
        }

        .spinner {
            width: 2rem;
            height: 2rem;
            border: 0.125rem solid var(--gray-200);
            border-top: 0.125rem solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Analysis Form */
        .analysis-form {
            display: flex;
            gap: 0.75rem;
            align-items: center;
            justify-content: center;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }

        .form-input {
            padding: 0.75rem 1rem;
            border: 1px solid var(--gray-300);
            border-radius: 0.5rem;
            font-size: 0.875rem;
            min-width: 200px;
            outline: none;
            transition: border-color 0.15s ease;
            box-shadow: var(--shadow-sm);
        }

        .form-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        /* Analysis Results */
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .metric-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--gray-200);
        }

        .metric-item:last-child {
            border-bottom: none;
        }

        .metric-label {
            font-weight: 500;
            color: var(--gray-700);
        }

        .metric-value {
            color: var(--gray-900);
            font-weight: 600;
        }

        /* Debug Section */
        .debug-section {
            background-color: var(--gray-100);
            border-radius: 0.5rem;
            padding: 1rem;
            margin-top: 1rem;
            font-size: 0.8125rem;
            max-height: 200px;
            overflow-y: auto;
        }

        .debug-section h3 {
            color: var(--gray-700);
            margin-bottom: 0.5rem;
        }

        .debug-section pre {
            white-space: pre-wrap;
            word-break: break-word;
            color: var(--gray-600);
        }

        /* Responsive */
        @media (max-width: 768px) {
            .container { padding: 0 1rem; }
            .header { padding: 1.5rem 0; margin-bottom: 1.5rem; }
            .header h1 { font-size: 2rem; }
            .controls { gap: 0.5rem; }
            .btn { padding: 0.625rem 1.25rem; font-size: 0.8125rem; }
            .tabs { flex-direction: column; }
            .tab { border-right: none; border-bottom: 1px solid var(--gray-200); }
            .tab:first-child, .tab:last-child { border-radius: 0; }
            .analysis-form { flex-direction: column; align-items: stretch; }
            .form-input { min-width: auto; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>Stock Scanner Pro</h1>
            <p class="subtitle">Two-Stage Analysis: Fundamental Quality + Technical Timing</p>
            <p class="description">Market Cap > ₹1 Cr • Quality Score > 3/10 • Technical Score > 30/100</p>
            <span class="status-badge">ROBUST VERSION 4.0</span>
        </div>
    </div>

    <div class="container">
        <div class="controls">
            <button class="btn btn-primary" onclick="startScan()" id="scanBtn">
                Start Complete Scan
            </button>
            <button class="btn btn-secondary" onclick="showTab('final')">
                Final Results
            </button>
            <button class="btn btn-secondary" onclick="showTab('fundamental')">
                Fundamental Results
            </button>
            <button class="btn btn-secondary" onclick="showDebug()">
                Show Debug Info
            </button>
        </div>
        
        <div class="card progress-section">
            <div class="stage-text" id="stage-text">Ready to start complete scan</div>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill" style="width: 0%;"></div>
            </div>
            <div class="progress-text" id="progress-text">Click "Start Complete Scan" to begin</div>
        </div>

        <div class="stats">
            <div class="card stat-card">
                <div class="stat-number" id="total-stocks">-</div>
                <div class="stat-label">Total Stocks Scanned</div>
            </div>
            <div class="card stat-card">
                <div class="stat-number" id="fundamental-passed">-</div>
                <div class="stat-label">Fundamental Filter Passed</div>
            </div>
            <div class="card stat-card">
                <div class="stat-number" id="technical-qualified">-</div>
                <div class="stat-label">Final Qualified</div>
            </div>
        </div>

        <div class="card results">
            <div class="tabs">
                <div class="tab active" onclick="showTab('final')">Final Results</div>
                <div class="tab" onclick="showTab('fundamental')">Fundamental Results</div>
                <div class="tab" onclick="showTab('analyze')">Analyze Stock</div>
            </div>

            <div id="final" class="tab-content active">
                <h2>Final Qualified Stocks</h2>
                <div id="final-content">
                    <div class="empty-state">
                        <div class="empty-icon">📊</div>
                        <p>Stocks passing both fundamental and technical filters will appear here</p>
                    </div>
                </div>
            </div>

            <div id="fundamental" class="tab-content">
                <h2>Fundamentally Sound Stocks</h2>
                <div id="fundamental-content">
                    <div class="empty-state">
                        <div class="empty-icon">📈</div>
                        <p>Stocks passing fundamental filter will appear here</p>
                    </div>
                </div>
            </div>

            <div id="analyze" class="tab-content">
                <h2>Individual Stock Analysis</h2>
                <div class="analysis-form">
                    <input 
                        type="text" 
                        id="stock-symbol" 
                        class="form-input" 
                        placeholder="Try: RELIANCE, TCS, HDFCBANK, INFY"
                        onkeypress="if(event.key==='Enter') analyzeStock()"
                    >
                    <button class="btn btn-primary" onclick="analyzeStock()">Analyze Stock</button>
                </div>
                <div id="analyze-content">
                    <div class="empty-state">
                        <div class="empty-icon">🔍</div>
                        <p>Enter a stock symbol to get detailed fundamental and technical analysis</p>
                        <p style="margin-top: 0.5rem; font-size: 0.875rem;">Try: RELIANCE, TCS, HDFCBANK, INFY, MARUTI</p>
                    </div>
                </div>
            </div>
        </div>

        <div id="debug-info" class="debug-section" style="display: none;">
            <h3>Debug Information</h3>
            <pre id="debug-content">No debug info available</pre>
        </div>
    </div>

    <script>
        let scanInterval;

        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        }

        async function startScan() {
            const scanBtn = document.getElementById('scanBtn');
            scanBtn.disabled = true;
            scanBtn.textContent = 'Scanning...';
            
            try {
                await fetch('/start-scan', {method: 'POST'});
                
                scanInterval = setInterval(async () => {
                    try {
                        const response = await fetch('/scan-status');
                        const data = await response.json();
                        
                        updateProgress(data);
                        
                        if (data.status === 'completed') {
                            clearInterval(scanInterval);
                            await loadResults();
                            scanBtn.disabled = false;
                            scanBtn.textContent = 'Start Complete Scan';
                        }
                    } catch (error) {
                        console.error('Status update error:', error);
                    }
                }, 3000);
                
            } catch (error) {
                console.error('Scan start error:', error);
                scanBtn.disabled = false;
                scanBtn.textContent = 'Start Complete Scan';
            }
        }

        function updateProgress(data) {
            const progress = data.progress || 0;
            document.getElementById('progress-fill').style.width = progress + '%';
            
            let stageText = '';
            switch(data.stage) {
                case 'fundamental_filtering':
                    stageText = 'Stage 1: Fundamental Analysis in Progress';
                    break;
                case 'technical_analysis':
                    stageText = 'Stage 2: Technical Analysis on Quality Stocks';
                    break;
                case 'completed':
                    stageText = 'Scan Complete';
                    break;
                default:
                    stageText = 'Ready to start complete scan';
            }
            
            document.getElementById('stage-text').textContent = stageText;
            document.getElementById('progress-text').textContent = `Progress: ${progress}%`;
            
            document.getElementById('total-stocks').textContent = data.total_stocks || '-';
            document.getElementById('fundamental-passed').textContent = data.fundamental_passed || '-';
            document.getElementById('technical-qualified').textContent = data.technical_qualified || '-';
        }

        async function loadResults() {
            try {
                const response = await fetch('/results');
                const data = await response.json();
                
                displayFinalResults(data.final_results || []);
                displayFundamentalResults(data.fundamental_results || []);
            } catch (error) {
                console.error('Error loading results:', error);
            }
        }

        async function showDebug() {
            try {
                const response = await fetch('/debug');
                const data = await response.json();
                
                const debugSection = document.getElementById('debug-info');
                const debugContent = document.getElementById('debug-content');
                
                debugContent.textContent = data.debug_info.join('\\n');
                debugSection.style.display = debugSection.style.display === 'none' ? 'block' : 'none';
            } catch (error) {
                console.error('Error loading debug info:', error);
            }
        }

        function displayFinalResults(stocks) {
            const content = document.getElementById('final-content');
            
            if (!stocks || stocks.length === 0) {
                content.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">📊</div>
                        <p>No stocks qualified both filters</p>
                        <p style="margin-top: 0.5rem; font-size: 0.875rem;">Try running a scan or check debug info</p>
                    </div>
                `;
                return;
            }

            let html = `<p style="margin-bottom: 1rem; color: var(--gray-600);">Found ${stocks.length} stocks passing both filters</p>`;
            html += `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Stock</th>
                                <th>Final Score</th>
                                <th>Fund Grade</th>
                                <th>Tech Score</th>
                                <th>Recommendation</th>
                                <th>Price</th>
                                <th>Market Cap</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            stocks.forEach(stock => {
                const gradeClass = getGradeBadgeClass(stock.grade);
                const recClass = getRecommendationClass(stock.recommendation);
                
                html += `
                    <tr>
                        <td>
                            <div class="company-info">
                                <div class="company-name">${stock.symbol}</div>
                                <div class="company-sector">${stock.sector || 'Unknown'}</div>
                            </div>
                        </td>
                        <td><strong>${stock.final_score || 0}</strong></td>
                        <td><span class="badge ${gradeClass}">${stock.grade || 'N/A'}</span></td>
                        <td>${stock.technical_score || 0}/100</td>
                        <td><span class="badge ${recClass}">${stock.recommendation || 'HOLD'}</span></td>
                        <td>₹${(stock.current_price || 0).toFixed(2)}</td>
                        <td>₹${(stock.market_cap_cr || 0).toLocaleString()} Cr</td>
                    </tr>
                `;
            });

            html += '</tbody></table></div>';
            content.innerHTML = html;
        }

        function displayFundamentalResults(stocks) {
            const content = document.getElementById('fundamental-content');
            
            if (!stocks || stocks.length === 0) {
                content.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">📈</div>
                        <p>No fundamental results available</p>
                        <p style="margin-top: 0.5rem; font-size: 0.875rem;">Try running a scan or check debug info</p>
                    </div>
                `;
                return;
            }

            let html = `<p style="margin-bottom: 1rem; color: var(--gray-600);">Found ${stocks.length} fundamentally sound stocks</p>`;
            html += `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Stock</th>
                                <th>Market Cap (₹Cr)</th>
                                <th>Score</th>
                                <th>Grade</th>
                                <th>P/E</th>
                                <th>ROE</th>
                                <th>Debt/Equity</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            stocks.slice(0, 50).forEach(stock => {
                const gradeClass = getGradeBadgeClass(stock.grade);
                
                html += `
                    <tr>
                        <td>
                            <div class="company-info">
                                <div class="company-name">${stock.symbol}</div>
                                <div class="company-sector">${stock.sector || 'Unknown'}</div>
                            </div>
                        </td>
                        <td>₹${(stock.market_cap_cr || 0).toLocaleString()}</td>
                        <td><strong>${(stock.score || 0).toFixed(1)}/10</strong></td>
                        <td><span class="badge ${gradeClass}">${stock.grade || 'N/A'}</span></td>
                        <td>${(stock.pe_ratio || 0).toFixed(1)}</td>
                        <td>${(stock.roe || 0).toFixed(1)}%</td>
                        <td>${(stock.debt_to_equity || 0).toFixed(2)}</td>
                    </tr>
                `;
            });

            html += '</tbody></table></div>';
            content.innerHTML = html;
        }

        async function analyzeStock() {
            const symbol = document.getElementById('stock-symbol').value.trim().toUpperCase();
            if (!symbol) {
                alert('Please enter a stock symbol');
                return;
            }
            
            document.getElementById('analyze-content').innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Analyzing ${symbol}...</p>
                </div>
            `;
            
            try {
                const response = await fetch(`/analyze/${symbol}`);
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('analyze-content').innerHTML = `
                        <div class="empty-state">
                            <div class="empty-icon" style="color: var(--danger);">❌</div>
                            <p><strong>Error:</strong> ${data.error}</p>
                        </div>
                    `;
                    return;
                }
                
                displayStockAnalysis(data);
                
            } catch (error) {
                document.getElementById('analyze-content').innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon" style="color: var(--danger);">❌</div>
                        <p><strong>Network Error:</strong> ${error.message}</p>
                    </div>
                `;
            }
        }

        function displayStockAnalysis(data) {
            const gradeClass = getGradeBadgeClass(data.grade);
            const recClass = getRecommendationClass(data.recommendation);
            
            let html = `
                <div class="analysis-grid">
                    <div class="card stat-card">
                        <div class="stat-number" style="font-size: 1.5rem;">${data.symbol}</div>
                        <div class="stat-label">${data.company_name || ''}</div>
                    </div>
                    <div class="card stat-card">
                        <div class="stat-number">₹${(data.market_cap_cr || 0).toLocaleString()}</div>
                        <div class="stat-label">Market Cap (Cr)</div>
                    </div>
                    <div class="card stat-card">
                        <div class="stat-number">${(data.score || 0).toFixed(1)}/10</div>
                        <div class="stat-label">Fundamental Score</div>
                    </div>
                    <div class="card stat-card">
                        <div class="stat-number">${data.technical_score || 0}/100</div>
                        <div class="stat-label">Technical Score</div>
                    </div>
                </div>
            `;
            
            html += `
                <div class="table-container">
                    <table>
                        <tbody>
                            <tr><td class="metric-label">Current Price</td><td class="metric-value">₹${(data.current_price || 0).toFixed(2)}</td></tr>
                            <tr><td class="metric-label">Quality Grade</td><td class="metric-value"><span class="badge ${gradeClass}">${data.grade || 'N/A'}</span></td></tr>
                            <tr><td class="metric-label">P/E Ratio</td><td class="metric-value">${(data.pe_ratio || 0).toFixed(1)}</td></tr>
                            <tr><td class="metric-label">ROE</td><td class="metric-value">${(data.roe || 0).toFixed(1)}%</td></tr>
                            <tr><td class="metric-label">Debt/Equity</td><td class="metric-value">${(data.debt_to_equity || 0).toFixed(2)}</td></tr>
                            <tr><td class="metric-label">Revenue Growth</td><td class="metric-value">${(data.revenue_growth || 0).toFixed(1)}%</td></tr>
                            <tr><td class="metric-label">Profit Margin</td><td class="metric-value">${(data.profit_margin || 0).toFixed(1)}%</td></tr>
                            <tr><td class="metric-label">Data Quality</td><td class="metric-value">${((data.data_completeness || 0) * 100).toFixed(0)}%</td></tr>
            `;
            
            if (data.rsi) {
                html += `<tr><td class="metric-label">RSI</td><td class="metric-value">${data.rsi}</td></tr>`;
            }
            if (data.recommendation && data.recommendation !== 'NO_TECHNICAL_DATA') {
                html += `<tr><td class="metric-label">Recommendation</td><td class="metric-value"><span class="badge ${recClass}">${data.recommendation}</span></td></tr>`;
            }
            if (data.final_score) {
                html += `<tr><td class="metric-label">Final Score</td><td class="metric-value"><strong>${data.final_score}</strong></td></tr>`;
            }
            
            html += '</tbody></table></div>';
            
            document.getElementById('analyze-content').innerHTML = html;
        }

        function getGradeBadgeClass(grade) {
            if (!grade) return 'badge-secondary';
            switch (grade.toUpperCase()) {
                case 'A+':
                case 'A':
                    return 'badge-success';
                case 'B+':
                case 'B':
                    return 'badge-info';
                case 'C+':
                case 'C':
                    return 'badge-warning';
                default:
                    return 'badge-danger';
            }
        }

        function getRecommendationClass(rec) {
            if (!rec) return 'badge-secondary';
            switch (rec.toUpperCase()) {
                case 'STRONG_BUY':
                    return 'badge-success';
                case 'BUY':
                    return 'badge-success';
                case 'HOLD':
                    return 'badge-info';
                case 'WEAK_HOLD':
                    return 'badge-warning';
                case 'AVOID':
                    return 'badge-danger';
                default:
                    return 'badge-secondary';
            }
        }
    </script>
</body>
</html>
""")

if __name__ == "__main__":
    import os, uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, log_level="info")
