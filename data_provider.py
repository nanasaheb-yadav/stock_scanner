import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any

class DataProvider:
    """Free data provider using Yahoo Finance API"""
    
    # Nifty 50 stocks with Yahoo Finance symbols
    NIFTY_50_STOCKS = {
        'ADANIPORTS.NS': 'Adani Ports and SEZ Ltd',
        'ASIANPAINT.NS': 'Asian Paints Ltd',
        'AXISBANK.NS': 'Axis Bank Ltd',
        'BAJAJ-AUTO.NS': 'Bajaj Auto Ltd',
        'BAJFINANCE.NS': 'Bajaj Finance Ltd',
        'BAJAJFINSV.NS': 'Bajaj Finserv Ltd',
        'BHARTIARTL.NS': 'Bharti Airtel Ltd',
        'BPCL.NS': 'Bharat Petroleum Corporation Ltd',
        'BRITANNIA.NS': 'Britannia Industries Ltd',
        'CIPLA.NS': 'Cipla Ltd',
        'COALINDIA.NS': 'Coal India Ltd',
        'DIVISLAB.NS': 'Divi\'s Laboratories Ltd',
        'DRREDDY.NS': 'Dr. Reddy\'s Laboratories Ltd',
        'EICHERMOT.NS': 'Eicher Motors Ltd',
        'GRASIM.NS': 'Grasim Industries Ltd',
        'HCLTECH.NS': 'HCL Technologies Ltd',
        'HDFCBANK.NS': 'HDFC Bank Ltd',
        'HDFCLIFE.NS': 'HDFC Life Insurance Company Ltd',
        'HEROMOTOCO.NS': 'Hero MotoCorp Ltd',
        'HINDALCO.NS': 'Hindalco Industries Ltd',
        'HINDUNILVR.NS': 'Hindustan Unilever Ltd',
        'ICICIBANK.NS': 'ICICI Bank Ltd',
        'ITC.NS': 'ITC Ltd',
        'INDUSINDBK.NS': 'IndusInd Bank Ltd',
        'INFY.NS': 'Infosys Ltd',
        'JSWSTEEL.NS': 'JSW Steel Ltd',
        'KOTAKBANK.NS': 'Kotak Mahindra Bank Ltd',
        'LT.NS': 'Larsen & Toubro Ltd',
        'M&M.NS': 'Mahindra & Mahindra Ltd',
        'MARUTI.NS': 'Maruti Suzuki India Ltd',
        'NESTLEIND.NS': 'Nestle India Ltd',
        'NTPC.NS': 'NTPC Ltd',
        'ONGC.NS': 'Oil & Natural Gas Corporation Ltd',
        'POWERGRID.NS': 'Power Grid Corporation of India Ltd',
        'RELIANCE.NS': 'Reliance Industries Ltd',
        'SBILIFE.NS': 'SBI Life Insurance Company Ltd',
        'SBIN.NS': 'State Bank of India',
        'SUNPHARMA.NS': 'Sun Pharmaceutical Industries Ltd',
        'TATACONSUM.NS': 'Tata Consumer Products Ltd',
        'TATAMOTORS.NS': 'Tata Motors Ltd',
        'TATASTEEL.NS': 'Tata Steel Ltd',
        'TCS.NS': 'Tata Consultancy Services Ltd',
        'TECHM.NS': 'Tech Mahindra Ltd',
        'TITAN.NS': 'Titan Company Ltd',
        'ULTRACEMCO.NS': 'UltraTech Cement Ltd',
        'UPL.NS': 'UPL Ltd',
        'WIPRO.NS': 'Wipro Ltd'
    }
    
    @staticmethod
    def get_stock_list() -> List[Dict[str, str]]:
        """Get list of stocks to scan"""
        return [
            {'symbol': symbol, 'name': name} 
            for symbol, name in DataProvider.NIFTY_50_STOCKS.items()
        ]
    
    @staticmethod
    def fetch_weekly_data(symbol: str, period: str = "2y") -> pd.DataFrame:
        """
        Fetch weekly historical data for a stock
        Args:
            symbol: Yahoo Finance symbol (e.g., 'RELIANCE.NS')
            period: Data period ('1y', '2y', '5y', 'max')
        Returns:
            DataFrame with Date, Open, High, Low, Close, Volume columns
        """
        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch weekly data
            hist = ticker.history(period=period, interval="1mo")  # Monthly data for weekly analysis
            
            if hist.empty:
                print(f"No data found for {symbol}")
                return pd.DataFrame()
            
            # Reset index to make Date a column
            hist.reset_index(inplace=True)
            
            # Standardize column names
            hist.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            
            # Ensure data is sorted by date
            hist = hist.sort_values('Date').reset_index(drop=True)
            
            return hist
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_current_price(symbol: str) -> float:
        """Get current/latest price for a stock"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.history(period="1d")
            
            if not info.empty:
                return float(info['Close'].iloc[-1])
            else:
                return 0.0
                
        except Exception as e:
            print(f"Error getting current price for {symbol}: {e}")
            return 0.0
    
    @staticmethod
    def get_stock_info(symbol: str) -> Dict[str, Any]:
        """Get basic stock information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', DataProvider.NIFTY_50_STOCKS.get(symbol, symbol)),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'current_price': info.get('currentPrice', 0)
            }
            
        except Exception as e:
            print(f"Error getting info for {symbol}: {e}")
            return {
                'symbol': symbol,
                'name': DataProvider.NIFTY_50_STOCKS.get(symbol, symbol),
                'sector': 'Unknown',
                'industry': 'Unknown',
                'market_cap': 0,
                'current_price': 0
            }
    
    @staticmethod
    def test_connection() -> bool:
        """Test if data provider is working"""
        try:
            # Try to fetch data for Reliance
            data = DataProvider.fetch_weekly_data('RELIANCE.NS', period="1y")
            return not data.empty
        except:
            return False