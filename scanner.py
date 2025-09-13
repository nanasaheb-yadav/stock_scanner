import asyncio
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Any
from data_provider import DataProvider
from technical_analysis import TechnicalAnalysis

class StockScanner:
    """Main stock scanning engine implementing relaxed 2-criteria methodology"""
    
    def __init__(self):
        self.last_scan_time = None
        self.scan_results = []
        self.scan_in_progress = False
        
    def run_daily_scan(self) -> Dict[str, Any]:
        """
        Run the complete daily scanning process
        Returns results with qualified stocks and scan metadata
        """
        if self.scan_in_progress:
            return {
                'status': 'scan_in_progress',
                'message': 'Another scan is currently running',
                'results': self.scan_results
            }
            
        try:
            self.scan_in_progress = True
            print(f"Starting daily scan at {datetime.now()}")
            
            # Get stock list
            stock_list = DataProvider.get_stock_list()
            
            qualified_stocks = []
            scan_metadata = {
                'scan_date': datetime.now().strftime('%Y-%m-%d'),
                'scan_time': datetime.now().strftime('%H:%M:%S IST'),
                'total_stocks_analyzed': 0,
                'qualified_stocks_found': 0,
                'errors': [],
                'minimum_criteria': 2  # Updated to reflect new requirement
            }
            
            # Analyze each stock
            for stock in stock_list:
                try:
                    symbol = stock['symbol']
                    name = stock['name']
                    
                    print(f"Analyzing {symbol}...")
                    
                    # Fetch weekly data
                    weekly_data = DataProvider.fetch_weekly_data(symbol, period="2y")
                    
                    if weekly_data.empty:
                        scan_metadata['errors'].append(f"No data available for {symbol}")
                        continue
                    
                    # Perform technical analysis
                    analysis_result = TechnicalAnalysis.analyze_stock(symbol, weekly_data)
                    
                    if analysis_result:
                        scan_metadata['total_stocks_analyzed'] += 1
                        
                        # Add stock name to result
                        analysis_result['name'] = name
                        
                        # Check if stock meets minimum 2 criteria (CHANGED FROM 5)
                        if analysis_result['criteria_met'] >= 2:  # Changed from 5 to 2
                            analysis_result['qualified'] = True
                            qualified_stocks.append(analysis_result)
                            print(f"✅ {symbol} QUALIFIED - {analysis_result['criteria_met']}/5 criteria met (minimum 2 required)")
                        else:
                            print(f"❌ {symbol} - {analysis_result['criteria_met']}/5 criteria met (needs minimum 2)")
                    else:
                        scan_metadata['errors'].append(f"Analysis failed for {symbol}")
                    
                except Exception as e:
                    error_msg = f"Error processing {symbol}: {str(e)}"
                    print(error_msg)
                    scan_metadata['errors'].append(error_msg)
                    continue
            
            # Sort qualified stocks by criteria met (descending) then by risk-reward ratio
            qualified_stocks.sort(key=lambda x: (x['criteria_met'], x['risk_reward']), reverse=True)
            
            scan_metadata['qualified_stocks_found'] = len(qualified_stocks)
            self.scan_results = qualified_stocks
            self.last_scan_time = datetime.now()
            
            print(f"\n✅ Scan completed! Found {len(qualified_stocks)} qualified stocks out of {scan_metadata['total_stocks_analyzed']} analyzed.")
            print(f"📊 Criteria Distribution:")
            
            # Show distribution of criteria matches
            criteria_distribution = {}
            for stock in qualified_stocks:
                criteria_count = stock['criteria_met']
                criteria_distribution[criteria_count] = criteria_distribution.get(criteria_count, 0) + 1
            
            for criteria_count in sorted(criteria_distribution.keys(), reverse=True):
                count = criteria_distribution[criteria_count]
                print(f"   {criteria_count}/5 criteria: {count} stocks")
            
            return {
                'status': 'success',
                'scan_metadata': scan_metadata,
                'qualified_stocks': qualified_stocks,
                'total_qualified': len(qualified_stocks),
                'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
                'criteria_distribution': criteria_distribution
            }
            
        except Exception as e:
            error_msg = f"Critical error in daily scan: {str(e)}"
            print(error_msg)
            return {
                'status': 'error',
                'message': error_msg,
                'qualified_stocks': [],
                'total_qualified': 0
            }
        
        finally:
            self.scan_in_progress = False
    
    def get_stock_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get detailed analysis for a specific stock"""
        try:
            # Fetch data for the stock
            weekly_data = DataProvider.fetch_weekly_data(symbol, period="2y")
            
            if weekly_data.empty:
                return {'error': f'No data available for {symbol}'}
            
            # Perform analysis
            analysis = TechnicalAnalysis.analyze_stock(symbol, weekly_data)
            
            if analysis:
                # Add additional info
                stock_info = DataProvider.get_stock_info(symbol)
                analysis.update(stock_info)
                
                # Update qualification status based on new criteria (2+ instead of 5)
                analysis['qualified'] = analysis['criteria_met'] >= 2
                
                return analysis
            else:
                return {'error': f'Analysis failed for {symbol}'}
                
        except Exception as e:
            return {'error': f'Error analyzing {symbol}: {str(e)}'}
    
    def get_portfolio_recommendations(self) -> Dict[str, Any]:
        """
        Generate portfolio recommendations based on qualified stocks
        Now includes stocks with 2+ criteria matches
        Maximum 20 positions, 5% allocation each
        """
        if not self.scan_results:
            return {
                'message': 'No qualified stocks found in last scan',
                'recommendations': []
            }
        
        # Categorize stocks by criteria strength
        perfect_stocks = [s for s in self.scan_results if s['criteria_met'] == 5]
        strong_stocks = [s for s in self.scan_results if s['criteria_met'] == 4] 
        good_stocks = [s for s in self.scan_results if s['criteria_met'] == 3]
        moderate_stocks = [s for s in self.scan_results if s['criteria_met'] == 2]
        
        print(f"Portfolio Analysis:")
        print(f"  Perfect (5/5): {len(perfect_stocks)} stocks")
        print(f"  Strong (4/5): {len(strong_stocks)} stocks") 
        print(f"  Good (3/5): {len(good_stocks)} stocks")
        print(f"  Moderate (2/5): {len(moderate_stocks)} stocks")
        
        # Prioritize higher criteria stocks, but include all 2+ criteria stocks
        prioritized_stocks = perfect_stocks + strong_stocks + good_stocks + moderate_stocks
        
        # Take top 20 stocks (max portfolio size)
        top_stocks = prioritized_stocks[:20]
        
        portfolio_recommendations = []
        total_allocation = 0
        
        for i, stock in enumerate(top_stocks, 1):
            # Adjust allocation based on criteria strength
            if stock['criteria_met'] == 5:
                allocation = 5.0  # Full allocation for perfect stocks
                risk_category = "HIGH CONFIDENCE"
            elif stock['criteria_met'] == 4:
                allocation = 4.0  # Slightly reduced for strong stocks
                risk_category = "STRONG"
            elif stock['criteria_met'] == 3:
                allocation = 3.0  # Moderate allocation
                risk_category = "MODERATE"
            else:  # 2 criteria
                allocation = 2.0  # Conservative allocation
                risk_category = "CONSERVATIVE"
            
            total_allocation += allocation
            
            portfolio_recommendations.append({
                'rank': i,
                'symbol': stock['symbol'],
                'name': stock.get('name', stock['symbol']),
                'current_price': stock['current_price'],
                'allocation_percent': allocation,
                'stop_loss': stock['stop_loss'],
                'target': stock['target'],
                'risk_reward': stock['risk_reward'],
                'criteria_met': stock['criteria_met'],
                'risk_category': risk_category,
                'entry_reason': f'Meets {stock["criteria_met"]}/5 technical criteria ({risk_category.lower()} setup)'
            })
        
        return {
            'portfolio_size': len(portfolio_recommendations),
            'total_allocation': total_allocation,
            'max_positions': 20,
            'recommendations': portfolio_recommendations,
            'criteria_breakdown': {
                'perfect_5_criteria': len(perfect_stocks),
                'strong_4_criteria': len(strong_stocks), 
                'good_3_criteria': len(good_stocks),
                'moderate_2_criteria': len(moderate_stocks)
            },
            'risk_management': {
                'allocation_strategy': 'Weighted by criteria strength (5%/4%/3%/2%)',
                'min_criteria_required': '2 out of 5 technical criteria',
                'stop_loss_rule': 'Below previous swing low',
                'position_sizing': 'Variable allocation based on setup strength',
                'rebalancing': 'Daily profit taking at 3%/6% gains'
            }
        }
    
    def is_market_time(self) -> bool:
        """Check if it's market hours (9:15 AM to 3:30 PM IST)"""
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        # Market hours: 9:15 AM to 3:30 PM IST
        market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_start <= now <= market_end
    
    def should_run_daily_scan(self) -> bool:
        """
        Check if daily scan should run
        Conditions: After 5 PM IST and not already run today
        """
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        # Check if it's after 5 PM IST
        scan_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
        
        if now < scan_time:
            return False
        
        # Check if scan already run today
        if self.last_scan_time:
            last_scan_date = self.last_scan_time.date()
            today = now.date()
            
            if last_scan_date >= today:
                return False
        
        return True
    
    def get_scan_status(self) -> Dict[str, Any]:
        """Get current scan status and statistics"""
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        # Get criteria distribution from last scan
        criteria_stats = {'2_criteria': 0, '3_criteria': 0, '4_criteria': 0, '5_criteria': 0}
        if self.scan_results:
            for stock in self.scan_results:
                criteria_count = stock['criteria_met']
                if criteria_count >= 2:
                    criteria_stats[f'{criteria_count}_criteria'] = criteria_stats.get(f'{criteria_count}_criteria', 0) + 1
        
        return {
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S IST'),
            'scan_in_progress': self.scan_in_progress,
            'last_scan_time': self.last_scan_time.strftime('%Y-%m-%d %H:%M:%S IST') if self.last_scan_time else 'Never',
            'qualified_stocks_count': len(self.scan_results),
            'minimum_criteria_required': 2,  # Updated
            'criteria_distribution': criteria_stats,
            'should_run_scan': self.should_run_daily_scan(),
            'market_hours': self.is_market_time(),
            'next_scan_time': '17:00 IST (Daily)'
        }
