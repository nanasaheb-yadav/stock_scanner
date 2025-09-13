import pandas as pd
import numpy as np
from typing import Dict, List, Any

class TechnicalAnalysis:
    """Complete technical analysis implementation for stock scanning"""
    
    @staticmethod
    def calculate_hma(data: pd.Series, period: int = 30) -> pd.Series:
        """
        Calculate Hull Moving Average (HMA)
        HMA = WMA(2*WMA(n/2) - WMA(n), sqrt(n))
        """
        try:
            half_period = int(period / 2)
            sqrt_period = int(np.sqrt(period))
            
            # Calculate WMA for half period
            wma_half = data.rolling(window=half_period).apply(
                lambda x: np.sum(x * np.arange(1, len(x) + 1)) / np.sum(np.arange(1, len(x) + 1))
            )
            
            # Calculate WMA for full period
            wma_full = data.rolling(window=period).apply(
                lambda x: np.sum(x * np.arange(1, len(x) + 1)) / np.sum(np.arange(1, len(x) + 1))
            )
            
            # Calculate raw HMA
            raw_hma = 2 * wma_half - wma_full
            
            # Final HMA with sqrt period
            hma = raw_hma.rolling(window=sqrt_period).apply(
                lambda x: np.sum(x * np.arange(1, len(x) + 1)) / np.sum(np.arange(1, len(x) + 1))
            )
            
            return hma
            
        except Exception as e:
            print(f"Error calculating HMA: {e}")
            return pd.Series([np.nan] * len(data))
    
    @staticmethod
    def calculate_custom_macd(data: pd.Series, fast: int = 3, slow: int = 21, signal: int = 9) -> Dict[str, pd.Series]:
        """
        Calculate custom MACD with settings (3, 21, 9)
        Returns MACD line, Signal line, and Histogram
        """
        try:
            # Calculate EMAs
            ema_fast = data.ewm(span=fast).mean()
            ema_slow = data.ewm(span=slow).mean()
            
            # MACD line
            macd_line = ema_fast - ema_slow
            
            # Signal line
            signal_line = macd_line.ewm(span=signal).mean()
            
            # Histogram
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }
            
        except Exception as e:
            print(f"Error calculating MACD: {e}")
            return {
                'macd': pd.Series([np.nan] * len(data)),
                'signal': pd.Series([np.nan] * len(data)),
                'histogram': pd.Series([np.nan] * len(data))
            }
    
    @staticmethod
    def calculate_modified_rsi(data: pd.Series, period: int = 9, sma_period: int = 3, wma_period: int = 21) -> Dict[str, pd.Series]:
        """
        Calculate modified RSI with dual moving averages
        - 9-period RSI
        - 3-day SMA of RSI
        - 21-day WMA of RSI
        """
        try:
            # Calculate price changes
            delta = data.diff()
            
            # Separate gains and losses
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            # Calculate RS and RSI
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # 3-day SMA of RSI
            sma_3 = rsi.rolling(window=sma_period).mean()
            
            # 21-day WMA of RSI
            weights = np.arange(1, wma_period + 1)
            wma_21 = rsi.rolling(window=wma_period).apply(
                lambda x: np.sum(x * weights) / np.sum(weights) if len(x) == wma_period else np.nan
            )
            
            return {
                'rsi': rsi,
                'sma_3': sma_3,
                'wma_21': wma_21
            }
            
        except Exception as e:
            print(f"Error calculating RSI: {e}")
            return {
                'rsi': pd.Series([np.nan] * len(data)),
                'sma_3': pd.Series([np.nan] * len(data)),
                'wma_21': pd.Series([np.nan] * len(data))
            }
    
    @staticmethod
    def analyze_stock(symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Complete 5-criteria analysis for a single stock
        Now qualifies stocks with 2+ criteria instead of all 5
        Returns analysis results and qualification status
        """
        try:
            if len(df) < 50:  # Need sufficient data
                return None
            
            # Sort by date to ensure proper calculation
            df = df.sort_values('Date').reset_index(drop=True)
            close_prices = df['Close']
            
            # Calculate technical indicators
            hma_30 = TechnicalAnalysis.calculate_hma(close_prices, 30)
            hma_44 = TechnicalAnalysis.calculate_hma(close_prices, 44)
            
            macd_data = TechnicalAnalysis.calculate_custom_macd(close_prices)
            rsi_data = TechnicalAnalysis.calculate_modified_rsi(close_prices)
            
            # Get latest values
            current_price = close_prices.iloc[-1]
            latest_hma_30 = hma_30.iloc[-1] if not pd.isna(hma_30.iloc[-1]) else 0
            latest_hma_44 = hma_44.iloc[-1] if not pd.isna(hma_44.iloc[-1]) else 0
            
            # Check criteria (same 5 criteria, but now qualify with 2+)
            criteria_met = 0
            criteria_details = {}
            
            # Criterion 1: HMA Trend (30 HMA showing uptrend)
            hma_trend_up = False
            if len(hma_30) >= 2 and not pd.isna(hma_30.iloc[-1]) and not pd.isna(hma_30.iloc[-2]):
                hma_trend_up = hma_30.iloc[-1] > hma_30.iloc[-2]
            
            if hma_trend_up:
                criteria_met += 1
            criteria_details['hma_trend'] = hma_trend_up
            
            # Criterion 2: Price Position (between 30 HMA and 44 HMA)
            price_position_ok = False
            if latest_hma_30 > 0 and latest_hma_44 > 0:
                price_position_ok = latest_hma_30 <= current_price <= latest_hma_44
            
            if price_position_ok:
                criteria_met += 1
            criteria_details['price_position'] = price_position_ok
            
            # Criterion 3: MACD Setup (8+ histogram bars below zero + crossover)
            macd_setup_ok = False
            histogram = macd_data['histogram']
            macd_line = macd_data['macd']
            signal_line = macd_data['signal']
            
            if len(histogram) >= 10:
                # Count recent histogram bars below zero
                recent_histogram = histogram.tail(20)  # Look at last 20 bars
                bars_below_zero = (recent_histogram < 0).sum()
                
                # Check for bullish crossover (MACD above signal)
                latest_macd = macd_line.iloc[-1] if not pd.isna(macd_line.iloc[-1]) else 0
                latest_signal = signal_line.iloc[-1] if not pd.isna(signal_line.iloc[-1]) else 0
                bullish_crossover = latest_macd > latest_signal
                
                macd_setup_ok = bars_below_zero >= 8 and bullish_crossover
            
            if macd_setup_ok:
                criteria_met += 1
            criteria_details['macd_setup'] = macd_setup_ok
            
            # Criterion 4: RSI Dual Crossover
            rsi_crossover_ok = False
            rsi = rsi_data['rsi']
            sma_3 = rsi_data['sma_3']
            wma_21 = rsi_data['wma_21']
            
            if not pd.isna(rsi.iloc[-1]) and not pd.isna(sma_3.iloc[-1]) and not pd.isna(wma_21.iloc[-1]):
                rsi_above_wma = rsi.iloc[-1] > wma_21.iloc[-1]
                sma_above_wma = sma_3.iloc[-1] > wma_21.iloc[-1]
                rsi_crossover_ok = rsi_above_wma and sma_above_wma
            
            if rsi_crossover_ok:
                criteria_met += 1
            criteria_details['rsi_crossover'] = rsi_crossover_ok
            
            # Criterion 5: Weekly Timeframe (always true for our weekly data)
            criteria_met += 1
            criteria_details['weekly_timeframe'] = True
            
            # Calculate risk-reward ratio
            if latest_hma_30 > 0:
                stop_loss = latest_hma_30 * 0.95  # 5% below HMA 30
                target = current_price * 1.15     # 15% above current price
                risk_reward = (target - current_price) / (current_price - stop_loss) if current_price > stop_loss else 0
            else:
                risk_reward = 0
                stop_loss = current_price * 0.95
                target = current_price * 1.15
            
            # Determine setup strength based on criteria count
            if criteria_met == 5:
                setup_strength = "PERFECT"
                confidence_level = "VERY HIGH"
            elif criteria_met == 4:
                setup_strength = "STRONG"  
                confidence_level = "HIGH"
            elif criteria_met == 3:
                setup_strength = "GOOD"
                confidence_level = "MODERATE"
            elif criteria_met == 2:
                setup_strength = "MODERATE"
                confidence_level = "CAUTIOUS"
            else:
                setup_strength = "WEAK"
                confidence_level = "LOW"
            
            return {
                'symbol': symbol,
                'current_price': float(current_price),
                'hma_30': float(latest_hma_30),
                'hma_44': float(latest_hma_44),
                'criteria_met': criteria_met,
                'criteria_details': criteria_details,
                'qualified': criteria_met >= 2,  # CHANGED: Now qualifies with 2+ criteria
                'setup_strength': setup_strength,
                'confidence_level': confidence_level,
                'risk_reward': round(risk_reward, 2),
                'stop_loss': round(stop_loss, 2),
                'target': round(target, 2),
                'analysis_date': df['Date'].iloc[-1].strftime('%Y-%m-%d') if 'Date' in df.columns else None
            }
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None
