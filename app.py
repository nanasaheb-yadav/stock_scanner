import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, List, Optional, Tuple
import asyncio
import warnings
warnings.filterwarnings('ignore')

app = FastAPI(title="Complete Stock Scanner - Fundamental + Technical Analysis")

# Global configuration
CONFIG = {
    'min_market_cap_cr': 50,  # Minimum 50 crores market cap
    'fundamental_score_threshold': 6,  # Out of 10
    'technical_score_threshold': 60,  # Out of 100
    'max_stocks_to_analyze': 600,
    'risk_free_rate': 0.06
}

# Global scan storage
scan_data = {
    "status": "idle",
    "stage": "ready",  # ready, fundamental_filtering, technical_analysis, completed
    "progress": 0,
    "total_stocks": 0,
    "fundamental_passed": 0,
    "technical_qualified": 0,
    "fundamental_results": [],
    "final_results": [],
    "last_update": None,
    "market_regime": "UNKNOWN"
}

# ==================== NSE STOCK FETCHER ====================

def get_all_nse_symbols():
    """Fetch all NSE symbols with fallback to comprehensive list"""
    symbols = set()
    
    # Method 1: Try NSE API
    try:
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            for stock in data.get('data', []):
                if stock.get('symbol'):
                    symbols.add(f"{stock['symbol']}.NS")
            print(f"Fetched {len(symbols)} symbols from NSE API")
    except Exception as e:
        print(f"NSE API failed: {e}")
    
    # Method 2: Try alternative sources
    try:
        # Get Nifty 100, 200, 500 indices
        indices = ["^NSEI", "^CNXIT", "^NSEBANK"]  # Add more as needed
        for index in indices:
            ticker = yf.Ticker(index)
            # This is a simplified approach - in reality you'd need more comprehensive fetching
    except:
        pass
    
    # Method 3: Comprehensive fallback list (Most liquid NSE stocks)
    major_nse_stocks = [
        # Nifty 50 Complete List
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
        
        # Next 100 - High Market Cap Stocks
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
        "3MINDIA.NS", "ACC.NS", "AIAENG.NS", "APLLTD.NS", "ALKEM.NS",
        "AMARAJABAT.NS", "ASHOKLEY.NS", "ASTRAL.NS", "ATUL.NS", "BAJAJHLDNG.NS",
        "BALKRISIND.NS", "BANDHANBNK.NS", "BATAINDIA.NS", "BHARATFORG.NS", "BHEL.NS",
        "BLUESTARCO.NS", "CEATLTD.NS", "CHAMBLFERT.NS", "CHENNPETRO.NS", "CROMPTON.NS",
        "CUMMINSIND.NS", "DEEPAKNITRITE.NS", "DIXON.NS", "EMAMILTD.NS", "ESCORTS.NS",
        "EXIDEIND.NS", "FORTIS.NS", "GLENMARK.NS", "GNFC.NS", "GRANULES.NS",
        "GUJGASLTD.NS", "HAL.NS", "HINDCOPPER.NS", "HINDZINC.NS", "HONAUT.NS",
        "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS",
        "INDIAMART.NS", "INOXLEISUR.NS", "IPCALAB.NS", "ISEC.NS", "JKCEMENT.NS",
        "JSWENERGY.NS", "JUSTDIAL.NS", "KAJARIACER.NS", "KANSAINER.NS", "KTKBANK.NS",
        "L&TFH.NS", "LALPATHLAB.NS", "LAURUSLABS.NS", "MANAPPURAM.NS", "MINDTREE.NS",
        "MOTHERSUMI.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", "NCCLTD.NS", "NH.NS",
        "NHPC.NS", "OBEROIRLTY.NS", "OIL.NS", "ORIENTBANK.NS", "PFIZER.NS",
        "PIIND.NS", "POLYCAB.NS", "PRESTIGE.NS", "PNBHOUSING.NS", "QUESS.NS",
        "RADICO.NS", "RAIN.NS", "RAMCOCEM.NS", "RPOWER.NS", "SANOFI.NS",
        "SCHAEFFLER.NS", "SHREECEM.NS", "STARCEMENT.NS", "SUDARSCHEM.NS", "SYMPHONY.NS",
        "THERMAX.NS", "THYROCARE.NS", "TIINDIA.NS", "TORNTPHARM.NS", "TORNTPOWER.NS",
        "TRENT.NS", "TRIDENT.NS", "UCOBANK.NS", "UJJIVAN.NS", "UNIONBANK.NS",
        "UNITECH.NS", "UBL.NS", "VEDL.NS", "VOLTAS.NS", "WABAG.NS",
        "WELCORP.NS", "WHIRLPOOL.NS", "YESBANK.NS", "ZEEL.NS", "ZENSARTECH.NS",
        
        # Mid-cap stocks (Market cap 1000-10000 cr)
        "360ONE.NS", "AARTIDRUGS.NS", "AAVAS.NS", "ABCAPITAL.NS", "ABFRL.NS",
        "ABSLAMC.NS", "ADANIGAS.NS", "ADANIPOWER.NS", "AKZOINDIA.NS", "ANGELONE.NS",
        "ANANTRAJ.NS", "APARINDS.NS", "APOLLOTYRE.NS", "ARVIND.NS", "ASTERDM.NS",
        "AUROPHARMA.NS", "AVANTIFEED.NS", "BAJAJCON.NS", "BASF.NS", "BEML.NS",
        "BHARTIHEXA.NS", "BIKAJI.NS", "BIRLAMONEY.NS", "BLUEDART.NS", "BRIGADE.NS",
        "CANFINHOME.NS", "CAPLIPOINT.NS", "CARBORUNIV.NS", "CCL.NS", "CENTRALBK.NS",
        "CENTURYPLY.NS", "CENTURYTEX.NS", "CESC.NS", "CGPOWER.NS", "CHALET.NS",
        "CHEMPLASTS.NS", "CIPLA.NS", "CUB.NS", "COFORGE.NS", "COROMANDEL.NS",
        "CREDITACC.NS", "CRISIL.NS", "CYIENT.NS", "DCMSHRIRAM.NS", "DELTACORP.NS",
        "DHANUKA.NS", "DISHTV.NS", "EASEMYTRIP.NS", "EDELWEISS.NS", "ENDURANCE.NS",
        "EQUITAS.NS", "ESABINDIA.NS", "FINEORG.NS", "FINCABLES.NS", "FINPIPE.NS",
        "FSL.NS", "GALAXYSURF.NS", "GARFIBRES.NS", "GILLETTE.NS", "GLAND.NS",
        "GLAXO.NS", "GPPL.NS", "GREENPANEL.NS", "GRINDWELL.NS", "GRSE.NS",
        "GSHIP.NS", "GTLINFRA.NS", "GUJALKALI.NS", "GULFOILLUB.NS", "HCC.NS",
        "HEIDELBERG.NS", "HERITGFOOD.NS", "HFCL.NS", "HGINFRA.NS", "HIMATSEIDE.NS",
        "HLEGLAS.NS", "HSIL.NS", "IBREALEST.NS", "IDBI.NS", "IFBIND.NS",
        "IIFL.NS", "INDOCO.NS", "INFIBEAM.NS", "INOXWIND.NS", "INTELLECT.NS",
        "IOB.NS", "IRCON.NS", "ITI.NS", "J&KBANK.NS", "JBCHEPHARM.NS",
        "JINDALSAW.NS", "JINDALSTEL.NS", "JKPAPER.NS", "JKTYRE.NS", "JMFINANCIL.NS",
        "JSL.NS", "KALPATPOWR.NS", "KARURVYSYA.NS", "KEC.NS", "KEI.NS",
        "KPRMILL.NS", "KRBL.NS", "LAXMIMACH.NS", "LINDEINDIA.NS", "LUXIND.NS",
        "MAGMA.NS", "MAHINDCIE.NS", "MAHLOG.NS", "MANINFRA.NS", "MAXHEALTH.NS",
        "MCDOWELL-N.NS", "MCX.NS", "MINDACORP.NS", "MOIL.NS", "NAVINFLUOR.NS",
        "NESCO.NS", "NETWORK18.NS", "NEWGEN.NS", "NLCINDIA.NS", "NOCIL.NS",
        "NRBBEARING.NS", "NUVOCO.NS", "OMAXE.NS", "ORIENTCEM.NS", "PANAMAPET.NS",
        "PERSISTENT.NS", "PGHL.NS", "PHOENIXLTD.NS", "PNBGILTS.NS", "PNCINFRA.NS",
        "POLYMED.NS", "PRSMJOHNSN.NS", "PSB.NS", "PTC.NS", "PVR.NS",
        "RALLIS.NS", "RATNAMANI.NS", "RAYMOND.NS", "RECLTD.NS", "RELAXO.NS",
        "RIIL.NS", "RITES.NS", "ROUTE.NS", "RUPA.NS", "SAGCEM.NS",
        "SCI.NS", "SEQUENT.NS", "SFL.NS", "SHILPAMED.NS", "SHOPERSTOP.NS",
        "SHYAMMETL.NS", "SOLARINDS.NS", "SONATSOFTW.NS", "SOUTHBANK.NS", "SPANDANA.NS",
        "SPARC.NS", "SPICEJET.NS", "STLTECH.NS", "SUBEXLTD.NS", "SUNDARMFIN.NS",
        "SUNDRMFAST.NS", "SUPRAJIT.NS", "SUVEN.NS", "SYNGENE.NS", "TEAMLEASE.NS",
        "TEXRAIL.NS", "TGBHOTELS.NS", "THEMISMED.NS", "TIMKEN.NS", "TIPSMUSIC.NS",
        "TTKPRESTIG.NS", "TV18BRDCST.NS", "UJJIVAN.NS", "VAKRANGEE.NS", "VARROC.NS",
        "VBL.NS", "VGUARD.NS", "VINATIORGA.NS", "VIPIND.NS", "VMART.NS",
        "WESTLIFE.NS", "WOCKPHARMA.NS"
    ]
    
    symbols.update(major_nse_stocks)
    
    # Return sorted list with duplicates removed
    final_symbols = sorted(list(symbols))
    print(f"Total NSE symbols loaded: {len(final_symbols)}")
    return final_symbols

# ==================== FUNDAMENTAL ANALYSIS ENGINE ====================

class FundamentalAnalyzer:
    
    @staticmethod
    def get_fundamental_data(symbol: str) -> Dict[str, any]:
        """Fetch comprehensive fundamental data for a stock"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get basic info
            info = ticker.info
            if not info or 'marketCap' not in info:
                return None
            
            # Market cap filter (50 crores minimum)
            market_cap = info.get('marketCap', 0)
            if market_cap < (CONFIG['min_market_cap_cr'] * 10000000):  # 50 cr = 500 million
                return None
            
            # Get financial statements
            try:
                financials = ticker.financials
                balance_sheet = ticker.balance_sheet
                cash_flow = ticker.cashflow
            except:
                financials = balance_sheet = cash_flow = pd.DataFrame()
            
            # Extract key fundamental metrics
            fundamental_data = {
                'symbol': symbol.replace('.NS', ''),
                'company_name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap_cr': round(market_cap / 10000000, 2),  # Convert to crores
                'current_price': info.get('currentPrice', 0),
                
                # Valuation Ratios
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'pb_ratio': info.get('priceToBook', 0),
                'price_to_sales': info.get('priceToSalesTrailing12Months', 0),
                'ev_to_ebitda': info.get('enterpriseToEbitda', 0),
                
                # Profitability Ratios
                'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                'roa': info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0,
                'profit_margin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,
                'operating_margin': info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') else 0,
                'gross_margin': info.get('grossMargins', 0) * 100 if info.get('grossMargins') else 0,
                
                # Financial Health
                'debt_to_equity': info.get('debtToEquity', 0),
                'current_ratio': info.get('currentRatio', 0),
                'quick_ratio': info.get('quickRatio', 0),
                'interest_coverage': info.get('interestCoverage', 0),
                
                # Growth Metrics
                'revenue_growth': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0,
                'earnings_growth': info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0,
                
                # Dividend Information
                'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'payout_ratio': info.get('payoutRatio', 0) * 100 if info.get('payoutRatio') else 0,
                
                # Other Metrics
                'book_value': info.get('bookValue', 0),
                'eps': info.get('trailingEps', 0),
                'beta': info.get('beta', 1.0),
                '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                '52_week_low': info.get('fiftyTwoWeekLow', 0),
            }
            
            return fundamental_data
            
        except Exception as e:
            print(f"Error fetching fundamentals for {symbol}: {e}")
            return None
    
    @staticmethod
    def calculate_fundamental_score(fund_data: Dict[str, any]) -> Dict[str, any]:
        """Calculate comprehensive fundamental score (0-10)"""
        if not fund_data:
            return {'score': 0, 'details': {}}
        
        score_components = {}
        total_score = 0
        max_score = 10
        
        try:
            # 1. Valuation Score (0-2 points)
            valuation_score = 0
            pe_ratio = fund_data.get('pe_ratio', 0)
            pb_ratio = fund_data.get('pb_ratio', 0)
            
            # P/E Score
            if 0 < pe_ratio < 15:
                valuation_score += 1.0  # Undervalued
            elif 15 <= pe_ratio < 25:
                valuation_score += 0.7  # Fair value
            elif 25 <= pe_ratio < 35:
                valuation_score += 0.3  # Overvalued
            
            # P/B Score
            if 0 < pb_ratio < 1.5:
                valuation_score += 1.0  # Undervalued
            elif 1.5 <= pb_ratio < 3:
                valuation_score += 0.5  # Fair value
            
            score_components['valuation'] = min(2.0, valuation_score)
            
            # 2. Profitability Score (0-2.5 points)
            profitability_score = 0
            roe = fund_data.get('roe', 0)
            roa = fund_data.get('roa', 0)
            profit_margin = fund_data.get('profit_margin', 0)
            
            # ROE Score
            if roe > 20:
                profitability_score += 1.0  # Excellent
            elif roe > 15:
                profitability_score += 0.8  # Good
            elif roe > 10:
                profitability_score += 0.5  # Average
            
            # ROA Score
            if roa > 10:
                profitability_score += 0.8
            elif roa > 5:
                profitability_score += 0.5
            
            # Profit Margin Score
            if profit_margin > 15:
                profitability_score += 0.7
            elif profit_margin > 10:
                profitability_score += 0.4
            elif profit_margin > 5:
                profitability_score += 0.2
            
            score_components['profitability'] = min(2.5, profitability_score)
            
            # 3. Financial Health Score (0-2 points)
            health_score = 0
            debt_equity = fund_data.get('debt_to_equity', 0)
            current_ratio = fund_data.get('current_ratio', 0)
            
            # Debt-to-Equity Score
            if debt_equity < 0.5:
                health_score += 1.0  # Low debt
            elif debt_equity < 1.0:
                health_score += 0.7  # Moderate debt
            elif debt_equity < 2.0:
                health_score += 0.3  # High debt
            
            # Current Ratio Score
            if current_ratio > 1.5:
                health_score += 1.0  # Good liquidity
            elif current_ratio > 1.0:
                health_score += 0.7  # Adequate liquidity
            elif current_ratio > 0.8:
                health_score += 0.3  # Tight liquidity
            
            score_components['financial_health'] = min(2.0, health_score)
            
            # 4. Growth Score (0-2 points)
            growth_score = 0
            revenue_growth = fund_data.get('revenue_growth', 0)
            earnings_growth = fund_data.get('earnings_growth', 0)
            
            # Revenue Growth Score
            if revenue_growth > 20:
                growth_score += 1.0  # High growth
            elif revenue_growth > 10:
                growth_score += 0.7  # Good growth
            elif revenue_growth > 5:
                growth_score += 0.4  # Moderate growth
            elif revenue_growth > 0:
                growth_score += 0.2  # Positive growth
            
            # Earnings Growth Score
            if earnings_growth > 25:
                growth_score += 1.0
            elif earnings_growth > 15:
                growth_score += 0.7
            elif earnings_growth > 5:
                growth_score += 0.4
            elif earnings_growth > 0:
                growth_score += 0.2
            
            score_components['growth'] = min(2.0, growth_score)
            
            # 5. Dividend & Management Score (0-1.5 points)
            dividend_score = 0
            dividend_yield = fund_data.get('dividend_yield', 0)
            payout_ratio = fund_data.get('payout_ratio', 0)
            
            # Dividend Yield Score
            if 2 <= dividend_yield <= 6:
                dividend_score += 0.8  # Healthy dividend
            elif 1 <= dividend_yield < 2:
                dividend_score += 0.5  # Moderate dividend
            elif dividend_yield > 6:
                dividend_score += 0.3  # High dividend (might be unsustainable)
            
            # Payout Ratio Score
            if 20 <= payout_ratio <= 60:
                dividend_score += 0.7  # Sustainable payout
            elif 10 <= payout_ratio < 20 or 60 < payout_ratio <= 80:
                dividend_score += 0.4  # Acceptable payout
            
            score_components['dividend_management'] = min(1.5, dividend_score)
            
            # Calculate total score
            total_score = sum(score_components.values())
            
            # Determine grade
            if total_score >= 8.5:
                grade = 'A+'
                quality = 'EXCELLENT'
            elif total_score >= 7.5:
                grade = 'A'
                quality = 'VERY_GOOD'
            elif total_score >= 6.5:
                grade = 'B+'
                quality = 'GOOD'
            elif total_score >= 5.5:
                grade = 'B'
                quality = 'ABOVE_AVERAGE'
            elif total_score >= 4.5:
                grade = 'C+'
                quality = 'AVERAGE'
            elif total_score >= 3.5:
                grade = 'C'
                quality = 'BELOW_AVERAGE'
            else:
                grade = 'D'
                quality = 'POOR'
            
            return {
                'total_score': round(total_score, 2),
                'max_score': max_score,
                'grade': grade,
                'quality': quality,
                'score_components': score_components,
                'passed_filter': total_score >= CONFIG['fundamental_score_threshold']
            }
            
        except Exception as e:
            print(f"Error calculating fundamental score: {e}")
            return {'total_score': 0, 'passed_filter': False}

# ==================== TECHNICAL ANALYSIS (Simplified Version) ====================

class TechnicalAnalyzer:
    
    @staticmethod
    def calculate_technical_score(symbol: str) -> Dict[str, any]:
        """Calculate technical analysis score for fundamentally sound stocks"""
        try:
            # Get weekly data
            ticker = yf.Ticker(symbol)
            weekly_data = ticker.history(period="1y", interval="1wk")
            
            if weekly_data.empty or len(weekly_data) < 20:
                return None
            
            close = weekly_data['Close']
            high = weekly_data['High']
            low = weekly_data['Low']
            volume = weekly_data['Volume']
            
            # Technical indicators
            sma_20 = close.rolling(20).mean()
            sma_50 = close.rolling(50).mean() if len(close) >= 50 else sma_20
            rsi = TechnicalAnalyzer.calculate_rsi(close, 14)
            macd, signal = TechnicalAnalyzer.calculate_macd(close)
            
            current_price = close.iloc[-1]
            
            # Score components (0-100)
            technical_score = 0
            max_technical_score = 100
            
            # 1. Trend Score (0-30 points)
            trend_score = 0
            if not pd.isna(sma_20.iloc[-1]) and current_price > sma_20.iloc[-1]:
                trend_score += 15  # Above 20-day SMA
            if not pd.isna(sma_50.iloc[-1]) and current_price > sma_50.iloc[-1]:
                trend_score += 15  # Above 50-day SMA
            
            # 2. Momentum Score (0-25 points)
            momentum_score = 0
            if not pd.isna(rsi.iloc[-1]):
                rsi_val = rsi.iloc[-1]
                if 40 <= rsi_val <= 60:
                    momentum_score += 15  # Neutral momentum
                elif 60 < rsi_val <= 70:
                    momentum_score += 25  # Strong positive momentum
                elif 30 <= rsi_val < 40:
                    momentum_score += 10  # Oversold recovery
            
            # 3. MACD Score (0-20 points)
            macd_score = 0
            if not pd.isna(macd.iloc[-1]) and not pd.isna(signal.iloc[-1]):
                if macd.iloc[-1] > signal.iloc[-1]:
                    macd_score += 20  # Bullish MACD
                else:
                    macd_score += 5   # Bearish MACD
            
            # 4. Volume Score (0-15 points)
            volume_score = 0
            avg_volume = volume.rolling(20).mean().iloc[-1]
            if volume.iloc[-1] > avg_volume * 1.2:
                volume_score += 15  # High volume confirmation
            elif volume.iloc[-1] > avg_volume:
                volume_score += 10  # Above average volume
            else:
                volume_score += 5   # Normal volume
            
            # 5. Price Position Score (0-10 points)
            price_score = 0
            week_high = high.rolling(52).max().iloc[-1]
            week_low = low.rolling(52).min().iloc[-1]
            price_position = (current_price - week_low) / (week_high - week_low) * 100
            
            if 70 <= price_position <= 90:
                price_score += 10  # Near highs but not overextended
            elif 50 <= price_position < 70:
                price_score += 8   # Upper half of range
            elif 30 <= price_position < 50:
                price_score += 5   # Middle range
            else:
                price_score += 3   # Lower range
            
            technical_score = trend_score + momentum_score + macd_score + volume_score + price_score
            
            # Determine recommendation
            if technical_score >= 85:
                recommendation = 'STRONG_BUY'
            elif technical_score >= 70:
                recommendation = 'BUY'
            elif technical_score >= 55:
                recommendation = 'HOLD'
            elif technical_score >= 40:
                recommendation = 'WEAK_HOLD'
            else:
                recommendation = 'AVOID'
            
            return {
                'symbol': symbol.replace('.NS', ''),
                'technical_score': technical_score,
                'recommendation': recommendation,
                'current_price': round(float(current_price), 2),
                'rsi': round(rsi.iloc[-1], 2) if not pd.isna(rsi.iloc[-1]) else 0,
                'price_position_52w': round(price_position, 1),
                'volume_surge': volume.iloc[-1] > avg_volume * 1.2,
                'qualified': technical_score >= CONFIG['technical_score_threshold']
            }
            
        except Exception as e:
            print(f"Error in technical analysis for {symbol}: {e}")
            return None
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd, signal

# ==================== MAIN SCANNING ENGINE ====================

def run_complete_scan():
    """Run two-stage scanning: Fundamental filtering then Technical analysis"""
    global scan_data
    
    scan_data['status'] = 'running'
    scan_data['stage'] = 'fundamental_filtering'
    scan_data['progress'] = 0
    
    try:
        # Stage 1: Get all NSE symbols
        print("Stage 1: Fetching NSE symbols...")
        all_symbols = get_all_nse_symbols()
        scan_data['total_stocks'] = len(all_symbols)
        
        # Stage 2: Fundamental filtering
        print(f"Stage 2: Fundamental analysis on {len(all_symbols)} stocks...")
        scan_data['stage'] = 'fundamental_filtering'
        fundamentally_sound_stocks = []
        
        for i, symbol in enumerate(all_symbols):
            try:
                # Progress update
                scan_data['progress'] = int((i / len(all_symbols)) * 50)  # 50% for fundamental stage
                
                # Get fundamental data
                fund_data = FundamentalAnalyzer.get_fundamental_data(symbol)
                if not fund_data:
                    continue
                
                # Calculate fundamental score
                fund_score = FundamentalAnalyzer.calculate_fundamental_score(fund_data)
                
                # Combine data
                combined_data = {**fund_data, **fund_score}
                
                if fund_score.get('passed_filter', False):
                    fundamentally_sound_stocks.append(combined_data)
                
                # Limit for performance (can be removed for full scan)
                if len(fundamentally_sound_stocks) >= 100:
                    break
                    
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue
        
        scan_data['fundamental_passed'] = len(fundamentally_sound_stocks)
        scan_data['fundamental_results'] = fundamentally_sound_stocks
        
        print(f"Stage 2 Complete: {len(fundamentally_sound_stocks)} stocks passed fundamental filter")
        
        # Stage 3: Technical analysis on fundamentally sound stocks
        print("Stage 3: Technical analysis on fundamentally sound stocks...")
        scan_data['stage'] = 'technical_analysis'
        
        final_qualified_stocks = []
        
        for i, fund_stock in enumerate(fundamentally_sound_stocks):
            try:
                # Progress update (50-100%)
                scan_data['progress'] = 50 + int((i / len(fundamentally_sound_stocks)) * 50)
                
                symbol = f"{fund_stock['symbol']}.NS"
                tech_analysis = TechnicalAnalyzer.calculate_technical_score(symbol)
                
                if tech_analysis and tech_analysis.get('qualified', False):
                    # Combine fundamental and technical data
                    combined_stock = {
                        **fund_stock,
                        **tech_analysis,
                        'final_score': round((fund_stock['total_score'] * 10 + tech_analysis['technical_score']) / 2, 1)
                    }
                    final_qualified_stocks.append(combined_stock)
                    
            except Exception as e:
                print(f"Error in technical analysis for {fund_stock['symbol']}: {e}")
                continue
        
        # Sort by final score
        final_qualified_stocks.sort(key=lambda x: x['final_score'], reverse=True)
        
        scan_data['technical_qualified'] = len(final_qualified_stocks)
        scan_data['final_results'] = final_qualified_stocks
        scan_data['status'] = 'completed'
        scan_data['stage'] = 'completed'
        scan_data['progress'] = 100
        scan_data['last_update'] = datetime.now().isoformat()
        
        print(f"Scan Complete! {len(final_qualified_stocks)} stocks qualified both filters")
        
    except Exception as e:
        print(f"Scan error: {e}")
        scan_data['status'] = 'error'
        scan_data['final_results'] = []

# ==================== API ENDPOINTS ====================

@app.get("/health")
def health():
    return JSONResponse({
        "status": "ok",
        "features": ["fundamental_analysis", "technical_analysis", "two_stage_filtering"],
        "min_market_cap_cr": CONFIG['min_market_cap_cr']
    })

@app.post("/start-complete-scan")
def start_complete_scan(background_tasks: BackgroundTasks):
    if scan_data["status"] == "running":
        return JSONResponse({
            "status": "already_running", 
            "stage": scan_data["stage"],
            "progress": scan_data["progress"]
        }, status_code=202)
    
    background_tasks.add_task(run_complete_scan)
    return JSONResponse({
        "status": "scan_started", 
        "message": "Two-stage scanning initiated: Fundamental filtering + Technical analysis"
    }, status_code=202)

@app.get("/scan-status")
def get_scan_status():
    return JSONResponse(scan_data)

@app.get("/fundamental-results")
def get_fundamental_results():
    return JSONResponse({
        "total_passed": scan_data.get('fundamental_passed', 0),
        "results": scan_data.get('fundamental_results', [])[:50]  # Limit to 50 for UI
    })

@app.get("/final-results")
def get_final_results():
    return JSONResponse({
        "total_qualified": scan_data.get('technical_qualified', 0),
        "results": scan_data.get('final_results', [])
    })

@app.get("/analyze-fundamental/{symbol}")
def analyze_fundamental_single(symbol: str):
    try:
        if not symbol.endswith('.NS'):
            symbol += '.NS'
        
        fund_data = FundamentalAnalyzer.get_fundamental_data(symbol)
        if not fund_data:
            return JSONResponse({"error": "No fundamental data available"}, status_code=404)
        
        fund_score = FundamentalAnalyzer.calculate_fundamental_score(fund_data)
        result = {**fund_data, **fund_score}
        
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/", response_class=HTMLResponse)
def homepage():
    return HTMLResponse(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Complete Stock Scanner - Fundamental + Technical</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff; min-height: 100vh; line-height: 1.6;
        }}
        .container {{ max-width: 1600px; margin: 0 auto; padding: 20px; }}
        .header {{ 
            text-align: center; margin-bottom: 40px; 
            background: rgba(0,0,0,0.2); padding: 40px; border-radius: 20px;
            backdrop-filter: blur(10px); box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        .header h1 {{ 
            font-size: 3.2em; margin-bottom: 15px; 
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }}
        .header p {{ font-size: 1.4em; opacity: 0.9; margin-bottom: 10px; }}
        .feature-highlight {{ 
            background: linear-gradient(135deg, #11998e, #38ef7d); 
            padding: 15px 25px; border-radius: 25px; display: inline-block;
            font-weight: bold; margin-top: 15px;
        }}
        
        .workflow-section {{ 
            background: rgba(0,0,0,0.2); border-radius: 15px; padding: 30px; 
            margin-bottom: 30px; backdrop-filter: blur(10px);
        }}
        .workflow-steps {{ 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; margin-top: 20px; 
        }}
        .step {{ 
            background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px;
            text-align: center; border: 2px solid rgba(255,255,255,0.2);
        }}
        .step-number {{ 
            background: linear-gradient(135deg, #667eea, #764ba2); 
            width: 40px; height: 40px; border-radius: 50%; 
            display: flex; align-items: center; justify-content: center;
            font-weight: bold; font-size: 1.2em; margin: 0 auto 15px;
        }}
        .step h3 {{ margin-bottom: 10px; color: #fff; }}
        .step p {{ font-size: 0.9em; opacity: 0.8; }}
        
        .controls {{ 
            display: flex; justify-content: center; gap: 25px; 
            margin-bottom: 40px; flex-wrap: wrap; 
        }}
        .btn {{ 
            padding: 18px 35px; border: none; border-radius: 10px; 
            cursor: pointer; font-size: 1.2em; font-weight: 600; 
            transition: all 0.3s; text-decoration: none; display: inline-block;
            box-shadow: 0 6px 20px rgba(0,0,0,0.3); position: relative; overflow: hidden;
        }}
        .btn:before {{
            content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s; z-index: 1;
        }}
        .btn:hover:before {{ left: 100%; }}
        .btn:hover {{ transform: translateY(-3px); box-shadow: 0 10px 30px rgba(0,0,0,0.4); }}
        .btn:disabled {{ background: #555; cursor: not-allowed; transform: none; }}
        .btn-primary {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .btn-success {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .btn-info {{ background: linear-gradient(135deg, #FF9800 0%, #FF5722 100%); }}
        .btn-warning {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        
        .progress-section {{ 
            background: rgba(0,0,0,0.2); border-radius: 15px; 
            padding: 25px; margin-bottom: 30px; backdrop-filter: blur(10px);
        }}
        .progress-bar {{ 
            width: 100%; height: 25px; background: rgba(0,0,0,0.3); 
            border-radius: 15px; overflow: hidden; margin: 15px 0; position: relative;
        }}
        .progress-fill {{ 
            height: 100%; background: linear-gradient(90deg, #11998e, #38ef7d); 
            transition: width 0.3s; border-radius: 15px; position: relative;
        }}
        .progress-fill:after {{
            content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.3) 50%, transparent 70%);
            animation: shimmer 2s infinite;
        }}
        @keyframes shimmer {{ 0% {{ transform: translateX(-100%); }} 100% {{ transform: translateX(100%); }} }}
        
        .stats-grid {{ 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; margin-bottom: 30px; 
        }}
        .stat-card {{ 
            background: rgba(0,0,0,0.2); padding: 25px; border-radius: 15px; 
            text-align: center; backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s; cursor: pointer;
        }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-number {{ font-size: 2.5em; font-weight: bold; margin-bottom: 10px; }}
        .stat-label {{ color: #ccc; font-size: 1em; }}
        
        .results-section {{ 
            background: rgba(0,0,0,0.2); border-radius: 15px; 
            padding: 30px; margin-bottom: 25px; backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .tabs {{ 
            display: flex; justify-content: center; margin-bottom: 25px; 
            background: rgba(0,0,0,0.3); border-radius: 12px; padding: 8px;
        }}
        .tab {{ 
            padding: 12px 25px; cursor: pointer; border-radius: 8px; 
            transition: all 0.3s; margin: 0 5px; font-weight: 500;
        }}
        .tab.active {{ background: rgba(255,255,255,0.2); color: #fff; }}
        .tab:hover {{ background: rgba(255,255,255,0.1); }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        
        .results-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .results-table th, .results-table td {{ 
            padding: 15px 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); 
        }}
        .results-table th {{ 
            background: rgba(0,0,0,0.3); font-weight: 600; position: sticky; top: 0;
        }}
        .results-table tr:hover {{ background: rgba(255,255,255,0.1); }}
        
        .score-badge {{ 
            padding: 6px 15px; border-radius: 20px; font-size: 0.9em; 
            font-weight: bold; display: inline-block; min-width: 60px; text-align: center;
        }}
        .score-excellent {{ background: #4CAF50; color: white; }}
        .score-very-good {{ background: #8BC34A; color: white; }}
        .score-good {{ background: #FF9800; color: white; }}
        .score-average {{ background: #FF5722; color: white; }}
        .score-below-average {{ background: #795548; color: white; }}
        .score-poor {{ background: #F44336; color: white; }}
        
        .recommendation {{ 
            font-weight: bold; padding: 8px 15px; border-radius: 8px; 
            display: inline-block; min-width: 100px; text-align: center;
        }}
        .rec-strong-buy {{ background: #4CAF50; color: white; }}
        .rec-buy {{ background: #8BC34A; color: white; }}
        .rec-hold {{ background: #FF9800; color: white; }}
        .rec-weak-hold {{ background: #FF5722; color: white; }}
        .rec-avoid {{ background: #F44336; color: white; }}
        
        .loading {{ text-align: center; padding: 50px; }}
        .spinner {{ 
            border: 4px solid rgba(255,255,255,0.3); border-top: 4px solid #fff; 
            border-radius: 50%; width: 60px; height: 60px; 
            animation: spin 1s linear infinite; margin: 0 auto 25px; 
        }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        
        .beginner-mode {{ background: rgba(76, 175, 80, 0.1); }}
        .professional-mode {{ background: rgba(103, 58, 183, 0.1); }}
        
        .mode-toggle {{ 
            text-align: center; margin: 20px 0;
        }}
        .mode-btn {{ 
            padding: 10px 20px; margin: 0 10px; border: 2px solid rgba(255,255,255,0.3);
            background: transparent; color: #fff; border-radius: 8px; cursor: pointer;
            transition: all 0.3s;
        }}
        .mode-btn.active {{ 
            background: rgba(255,255,255,0.2); border-color: rgba(255,255,255,0.6);
        }}
        
        .tooltip {{ 
            position: relative; display: inline-block; cursor: help;
        }}
        .tooltip .tooltiptext {{ 
            visibility: hidden; width: 250px; background-color: rgba(0,0,0,0.9);
            color: #fff; text-align: center; border-radius: 8px; padding: 8px;
            position: absolute; z-index: 1; bottom: 125%; left: 50%;
            margin-left: -125px; opacity: 0; transition: opacity 0.3s;
        }}
        .tooltip:hover .tooltiptext {{ visibility: visible; opacity: 1; }}
        
        #scan-stage {{ 
            font-size: 1.3em; margin: 15px 0; text-align: center; 
            padding: 15px; border-radius: 10px; background: rgba(0,0,0,0.3);
        }}
        .stage-fundamental {{ color: #FF9800; }}
        .stage-technical {{ color: #2196F3; }}
        .stage-completed {{ color: #4CAF50; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Complete Stock Scanner Pro</h1>
            <p>Two-Stage Analysis: Fundamental Filtering + Advanced Technical Analysis</p>
            <p>Smart screening with Market Cap > ₹50 Cr + Quality Score > 6/10</p>
            <div class="feature-highlight">
                📊 Fundamental Analysis → 🔬 Technical Analysis → 💎 Final Recommendations
            </div>
        </div>
        
        <div class="mode-toggle">
            <button class="mode-btn active" onclick="setMode('beginner')">👶 Beginner Mode</button>
            <button class="mode-btn" onclick="setMode('professional')">👨‍💼 Professional Mode</button>
        </div>
        
        <div class="workflow-section">
            <h2 style="text-align: center; margin-bottom: 25px;">📋 Two-Stage Scanning Process</h2>
            <div class="workflow-steps">
                <div class="step">
                    <div class="step-number">1</div>
                    <h3>NSE Stock Universe</h3>
                    <p>Fetch all NSE listed stocks dynamically from multiple sources</p>
                </div>
                <div class="step">
                    <div class="step-number">2</div>
                    <h3>Fundamental Filter</h3>
                    <p>Market Cap > ₹50 Cr + Quality Score 6+/10 (P/E, ROE, Debt, Growth)</p>
                </div>
                <div class="step">
                    <div class="step-number">3</div>
                    <h3>Technical Analysis</h3>
                    <p>Advanced indicators on fundamentally sound stocks only</p>
                </div>
                <div class="step">
                    <div class="step-number">4</div>
                    <h3>Final Recommendations</h3>
                    <p>Combined scores with risk-adjusted position sizing</p>
                </div>
            </div>
        </div>

        <div class="controls">
            <button class="btn btn-primary" onclick="startCompleteScan()" id="scanBtn">
                🚀 Start Complete Scan
            </button>
            <button class="btn btn-success" onclick="showTab('final-results')">
                📈 Final Results
            </button>
            <button class="btn btn-info" onclick="showTab('fundamental-results')">
                📊 Fundamental Analysis
            </button>
            <button class="btn btn-warning" onclick="analyzeCustomStock()">
                🔍 Analyze Stock
            </button>
        </div>
        
        <div class="progress-section">
            <div id="scan-stage">Ready to scan NSE universe...</div>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill" style="width: 0%;"></div>
            </div>
            <div id="progress-text">Click "Start Complete Scan" to begin</div>
        </div>

        <div class="stats-grid">
            <div class="stat-card tooltip">
                <div class="stat-number" id="total-stocks" style="color: #2196F3;">-</div>
                <div class="stat-label">Total NSE Stocks</div>
                <span class="tooltiptext">All stocks fetched from NSE for analysis</span>
            </div>
            <div class="stat-card tooltip">
                <div class="stat-number" id="fundamental-passed" style="color: #FF9800;">-</div>
                <div class="stat-label">Fundamental Filter Passed</div>
                <span class="tooltiptext">Stocks with Market Cap > ₹50 Cr and Quality Score > 6/10</span>
            </div>
            <div class="stat-card tooltip">
                <div class="stat-number" id="technical-qualified" style="color: #4CAF50;">-</div>
                <div class="stat-label">Final Qualified</div>
                <span class="tooltiptext">Stocks passing both fundamental and technical filters</span>
            </div>
            <div class="stat-card tooltip">
                <div class="stat-number" id="avg-final-score" style="color: #9C27B0;">-</div>
                <div class="stat-label">Average Final Score</div>
                <span class="tooltiptext">Combined fundamental + technical score</span>
            </div>
        </div>

        <div class="results-section">
            <div class="tabs">
                <div class="tab active" onclick="showTab('final-results')">🎯 Final Results</div>
                <div class="tab" onclick="showTab('fundamental-results')">📊 Fundamental Analysis</div>
                <div class="tab" onclick="showTab('custom-analysis')">🔍 Custom Analysis</div>
            </div>

            <div id="final-results" class="tab-content active">
                <h2>🎯 Final Qualified Stocks (Fundamental + Technical)</h2>
                <div id="final-results-content">
                    <p style="text-align: center; color: #ccc; padding: 50px;">
                        Complete scan will show stocks that pass both fundamental and technical filters...
                    </p>
                </div>
            </div>

            <div id="fundamental-results" class="tab-content">
                <h2>📊 Fundamentally Sound Stocks (Market Cap > ₹50 Cr)</h2>
                <div id="fundamental-results-content">
                    <p style="text-align: center; color: #ccc; padding: 50px;">
                        Fundamental analysis results will appear here...
                    </p>
                </div>
            </div>

            <div id="custom-analysis" class="tab-content">
                <h2>🔍 Individual Stock Analysis</h2>
                <div style="text-align: center; margin-bottom: 25px;">
                    <input type="text" id="stock-symbol" placeholder="Enter stock symbol (e.g., RELIANCE)" 
                           style="padding: 15px; border-radius: 8px; border: none; width: 250px; margin-right: 15px; color: #333;">
                    <button class="btn btn-primary" onclick="analyzeIndividualStock()">Analyze</button>
                </div>
                <div id="custom-analysis-content">
                    <p style="text-align: center; color: #ccc; padding: 50px;">
                        Enter a stock symbol to get comprehensive fundamental + technical analysis...
                    </p>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentMode = 'beginner';
        let scanInterval;

        function setMode(mode) {{
            currentMode = mode;
            document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            document.body.className = mode === 'beginner' ? 'beginner-mode' : 'professional-mode';
            
            // Adjust UI complexity based on mode
            const professionalElements = document.querySelectorAll('.professional-only');
            professionalElements.forEach(el => {{
                el.style.display = mode === 'professional' ? 'block' : 'none';
            }});
        }}

        function showTab(tabName) {{
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        }}

        async function startCompleteScan() {{
            document.getElementById('scanBtn').disabled = true;
            document.getElementById('scanBtn').textContent = '🔄 Scanning...';
            
            try {{
                await fetch('/start-complete-scan', {{method: 'POST'}});
                
                scanInterval = setInterval(async () => {{
                    const response = await fetch('/scan-status');
                    const data = await response.json();
                    
                    updateScanProgress(data);
                    
                    if (data.status === 'completed') {{
                        clearInterval(scanInterval);
                        await loadFinalResults();
                        await loadFundamentalResults();
                        document.getElementById('scanBtn').disabled = false;
                        document.getElementById('scanBtn').textContent = '🚀 Start Complete Scan';
                    }}
                }}, 3000);
                
            }} catch (error) {{
                console.error('Scan error:', error);
                document.getElementById('scanBtn').disabled = false;
                document.getElementById('scanBtn').textContent = '🚀 Start Complete Scan';
            }}
        }}

        function updateScanProgress(data) {{
            const progress = data.progress || 0;
            document.getElementById('progress-fill').style.width = progress + '%';
            
            // Update stage display
            const stageElement = document.getElementById('scan-stage');
            let stageText = '';
            let stageClass = '';
            
            switch(data.stage) {{
                case 'fundamental_filtering':
                    stageText = '📊 Stage 1: Fundamental Analysis in Progress...';
                    stageClass = 'stage-fundamental';
                    break;
                case 'technical_analysis':
                    stageText = '🔬 Stage 2: Technical Analysis on Quality Stocks...';
                    stageClass = 'stage-technical';
                    break;
                case 'completed':
                    stageText = '✅ Scan Complete! Both stages finished.';
                    stageClass = 'stage-completed';
                    break;
                default:
                    stageText = 'Ready to scan NSE universe...';
                    stageClass = '';
            }}
            
            stageElement.textContent = stageText;
            stageElement.className = stageClass;
            
            // Update stats
            document.getElementById('total-stocks').textContent = data.total_stocks || 0;
            document.getElementById('fundamental-passed').textContent = data.fundamental_passed || 0;
            document.getElementById('technical-qualified').textContent = data.technical_qualified || 0;
            
            document.getElementById('progress-text').textContent = 
                `Progress: ${{progress}}% - ${{data.stage.replace('_', ' ')}}`;
        }}

        async function loadFinalResults() {{
            try {{
                const response = await fetch('/final-results');
                const data = await response.json();
                displayFinalResults(data.results || []);
                
                if (data.results && data.results.length > 0) {{
                    const avgScore = data.results.reduce((sum, stock) => 
                        sum + (stock.final_score || 0), 0) / data.results.length;
                    document.getElementById('avg-final-score').textContent = Math.round(avgScore);
                }}
            }} catch (error) {{
                console.error('Error loading final results:', error);
            }}
        }}

        async function loadFundamentalResults() {{
            try {{
                const response = await fetch('/fundamental-results');
                const data = await response.json();
                displayFundamentalResults(data.results || []);
            }} catch (error) {{
                console.error('Error loading fundamental results:', error);
            }}
        }}

        function displayFinalResults(stocks) {{
            const content = document.getElementById('final-results-content');
            
            if (!stocks || stocks.length === 0) {{
                content.innerHTML = '<p style="text-align: center; color: #ccc; padding: 50px;">No stocks qualified both filters.</p>';
                return;
            }}

            let html = `<div style="margin-bottom: 20px;">🎯 Found ${{stocks.length}} stocks passing both fundamental and technical filters</div>`;
            html += '<table class="results-table"><thead><tr>';
            html += '<th>Stock</th><th>Sector</th><th>Market Cap (₹Cr)</th><th>Final Score</th>';
            html += '<th>Fundamental Grade</th><th>Technical Score</th><th>Recommendation</th>';
            html += '<th>Current Price</th><th>P/E Ratio</th><th>ROE</th>';
            html += '</tr></thead><tbody>';

            stocks.forEach(stock => {{
                const finalScore = stock.final_score || 0;
                const scoreClass = finalScore >= 80 ? 'score-excellent' : 
                                 finalScore >= 70 ? 'score-very-good' : 
                                 finalScore >= 60 ? 'score-good' : 'score-average';
                                 
                const recClass = (stock.recommendation || '').toLowerCase().replace('_', '-');
                const gradeClass = `score-${{(stock.quality || 'average').toLowerCase().replace('_', '-')}}`;
                
                html += `<tr>
                    <td><strong>${{stock.symbol || stock.company_name}}</strong><br><small>${{stock.company_name || ''}}</small></td>
                    <td>${{stock.sector || 'Unknown'}}</td>
                    <td>₹${{(stock.market_cap_cr || 0).toLocaleString()}}</td>
                    <td><span class="score-badge ${{scoreClass}}">${{Math.round(finalScore)}}</span></td>
                    <td><span class="score-badge ${{gradeClass}}">${{stock.grade || 'N/A'}}</span></td>
                    <td>${{stock.technical_score || 0}}/100</td>
                    <td><span class="recommendation rec-${{recClass}}">${{stock.recommendation || 'HOLD'}}</span></td>
                    <td>₹${{(stock.current_price || 0).toFixed(2)}}</td>
                    <td>${{(stock.pe_ratio || 0).toFixed(1)}}</td>
                    <td>${{(stock.roe || 0).toFixed(1)}}%</td>
                </tr>`;
            }});

            html += '</tbody></table>';
            content.innerHTML = html;
        }}

        function displayFundamentalResults(stocks) {{
            const content = document.getElementById('fundamental-results-content');
            
            if (!stocks || stocks.length === 0) {{
                content.innerHTML = '<p style="text-align: center; color: #ccc; padding: 50px;">No fundamental results available.</p>';
                return;
            }}

            let html = `<div style="margin-bottom: 20px;">📊 Found ${{stocks.length}} fundamentally sound stocks (Market Cap > ₹50 Cr, Quality Score > 6/10)</div>`;
            html += '<table class="results-table"><thead><tr>';
            html += '<th>Stock</th><th>Sector</th><th>Market Cap (₹Cr)</th><th>Quality Score</th><th>Grade</th>';
            html += '<th>P/E Ratio</th><th>ROE</th><th>Debt/Equity</th><th>Revenue Growth</th><th>Dividend Yield</th>';
            html += '</tr></thead><tbody>';

            stocks.slice(0, 50).forEach(stock => {{  // Show top 50
                const score = stock.total_score || 0;
                const gradeClass = `score-${{(stock.quality || 'average').toLowerCase().replace('_', '-')}}`;
                
                html += `<tr>
                    <td><strong>${{stock.symbol}}</strong><br><small>${{stock.company_name || ''}}</small></td>
                    <td>${{stock.sector || 'Unknown'}}</td>
                    <td>₹${{(stock.market_cap_cr || 0).toLocaleString()}}</td>
                    <td><span class="score-badge ${{gradeClass}}">${{score.toFixed(1)}}/10</span></td>
                    <td><span class="score-badge ${{gradeClass}}">${{stock.grade || 'N/A'}}</span></td>
                    <td>${{(stock.pe_ratio || 0).toFixed(1)}}</td>
                    <td>${{(stock.roe || 0).toFixed(1)}}%</td>
                    <td>${{(stock.debt_to_equity || 0).toFixed(2)}}</td>
                    <td>${{(stock.revenue_growth || 0).toFixed(1)}}%</td>
                    <td>${{(stock.dividend_yield || 0).toFixed(2)}}%</td>
                </tr>`;
            }});

            html += '</tbody></table>';
            content.innerHTML = html;
        }}

        async function analyzeIndividualStock() {{
            const symbol = document.getElementById('stock-symbol').value.trim().toUpperCase();
            if (!symbol) {{
                alert('Please enter a stock symbol');
                return;
            }}
            
            document.getElementById('custom-analysis-content').innerHTML = 
                '<div class="loading"><div class="spinner"></div><p>Analyzing ' + symbol + '...</p></div>';
            
            try {{
                const response = await fetch(`/analyze-fundamental/${{symbol}}`);
                const data = await response.json();
                
                if (data.error) {{
                    document.getElementById('custom-analysis-content').innerHTML = 
                        '<p style="color: #F44336; text-align: center; padding: 40px;">Analysis Error: ' + data.error + '</p>';
                    return;
                }}
                
                displayCustomAnalysis(data);
                
            }} catch (error) {{
                document.getElementById('custom-analysis-content').innerHTML = 
                    '<p style="color: #F44336; text-align: center; padding: 40px;">Error: ' + error.message + '</p>';
            }}
        }}

        function displayCustomAnalysis(data) {{
            const gradeClass = `score-${{(data.quality || 'average').toLowerCase().replace('_', '-')}}`;
            
            let html = `<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px;">`;
            
            html += `<div class="stat-card">
                <h3>${{data.symbol}}</h3>
                <div class="stat-number">₹${{(data.market_cap_cr || 0).toLocaleString()}}</div>
                <div class="stat-label">Market Cap (Crores)</div>
            </div>`;
            
            html += `<div class="stat-card">
                <div class="stat-number score-badge ${{gradeClass}}">${{(data.total_score || 0).toFixed(1)}}/10</div>
                <div class="stat-label">Quality Score</div>
            </div>`;
            
            html += `<div class="stat-card">
                <div class="stat-number score-badge ${{gradeClass}}">${{data.grade || 'N/A'}}</div>
                <div class="stat-label">Quality Grade</div>
            </div>`;
            
            html += `<div class="stat-card">
                <div class="stat-number">${{data.passed_filter ? '✅' : '❌'}}</div>
                <div class="stat-label">Fundamental Filter</div>
            </div>`;
            
            html += '</div>';
            
            // Detailed breakdown
            html += '<h3>Detailed Fundamental Analysis</h3>';
            html += '<table class="results-table"><tbody>';
            html += `<tr><td><strong>Company</strong></td><td>${{data.company_name || data.symbol}}</td></tr>`;
            html += `<tr><td><strong>Sector</strong></td><td>${{data.sector || 'Unknown'}}</td></tr>`;
            html += `<tr><td><strong>Current Price</strong></td><td>₹${{(data.current_price || 0).toFixed(2)}}</td></tr>`;
            html += `<tr><td><strong>P/E Ratio</strong></td><td>${{(data.pe_ratio || 0).toFixed(1)}}</td></tr>`;
            html += `<tr><td><strong>P/B Ratio</strong></td><td>${{(data.pb_ratio || 0).toFixed(2)}}</td></tr>`;
            html += `<tr><td><strong>ROE</strong></td><td>${{(data.roe || 0).toFixed(1)}}%</td></tr>`;
            html += `<tr><td><strong>ROA</strong></td><td>${{(data.roa || 0).toFixed(1)}}%</td></tr>`;
            html += `<tr><td><strong>Debt to Equity</strong></td><td>${{(data.debt_to_equity || 0).toFixed(2)}}</td></tr>`;
            html += `<tr><td><strong>Current Ratio</strong></td><td>${{(data.current_ratio || 0).toFixed(2)}}</td></tr>`;
            html += `<tr><td><strong>Revenue Growth</strong></td><td>${{(data.revenue_growth || 0).toFixed(1)}}%</td></tr>`;
            html += `<tr><td><strong>Profit Margin</strong></td><td>${{(data.profit_margin || 0).toFixed(1)}}%</td></tr>`;
            html += `<tr><td><strong>Dividend Yield</strong></td><td>${{(data.dividend_yield || 0).toFixed(2)}}%</td></tr>`;
            html += `<tr><td><strong>Beta</strong></td><td>${{(data.beta || 0).toFixed(2)}}</td></tr>`;
            html += '</tbody></table>';
            
            // Score breakdown
            if (data.score_components) {{
                html += '<h3 style="margin-top: 20px;">Score Breakdown</h3>';
                html += '<table class="results-table"><tbody>';
                Object.entries(data.score_components).forEach(([component, score]) => {{
                    html += `<tr><td><strong>${{component.replace('_', ' ').toUpperCase()}}</strong></td><td>${{score.toFixed(2)}} points</td></tr>`;
                }});
                html += '</tbody></table>';
            }}
            
            document.getElementById('custom-analysis-content').innerHTML = html;
        }}

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            setMode('beginner');
        }});

        // Auto-refresh every 30 seconds during scan
        setInterval(async () => {{
            if (scanInterval) {{
                const response = await fetch('/scan-status');
                const data = await response.json();
                if (data.status === 'completed') {{
                    await loadFinalResults();
                    await loadFundamentalResults();
                }}
            }}
        }}, 30000);
    </script>
</body>
</html>
""")

if __name__ == "__main__":
    import os, uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, log_level="info")
