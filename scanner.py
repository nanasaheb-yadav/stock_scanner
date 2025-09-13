import asyncio
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Any
from data_provider import DataProvider
from technical_analysis import TechnicalAnalysis

class StockScanner:
    """Enhanced stock scanning engine for Nifty 500+ coverage"""
    
    def __init__(self):
        self.last_scan_time = None
        self.scan_results = []
        self.scan_in_progress = False
        
    def run_daily_scan(self, batch_mode: bool = True) -> Dict[str, Any]:
        """
        Run the complete daily scanning process for Nifty 500+ stocks
        Args:
            batch_mode: If True, processes stocks in batches to manage memory/API limits
        """
        if self.scan_in_progress:
            return {
                'status': 'scan_in_progress',
                'message': 'Another scan is currently running',
                'results': self.scan_results
            }
            
        try:
            self.scan_in_progress = True
            start_time = datetime.now()
            print(f"Starting comprehensive Nifty 500+ scan at {start_time}")
            
            # Get complete stock list
            all_stocks = DataProvider.get_stock_list()
            total_stocks = len(all_stocks)
            
            print(f"📊 Scanning {total_stocks} stocks from Nifty 500+ universe")
            print(f"🏢 Sector breakdown: {DataProvider.get_sector_breakdown()}")
            
            qualified_stocks = []
            scan_metadata = {
                'scan_date': datetime.now().strftime('%Y-%m-%d'),
                'scan_time': datetime.now().strftime('%H:%M:%S IST'),
                'total_stocks_to_scan': total_stocks,
                'total_stocks_analyzed': 0,
                'qualified_stocks_found': 0,
                'errors': [],
                'minimum_criteria': 2,
                'batch_mode': batch_mode,
                'sectors_covered': len(DataProvider.get_sector_breakdown())
            }
            
            # Process stocks in batches to manage API rate limits
            batch_size = 25 if batch_mode else len(all_stocks)
            batches = [all_stocks[i:i + batch_size] for i in range(0, len(all_stocks), batch_size)]
            
            print(f"🔄 Processing {len(batches)} batches of {batch_size} stocks each...")
            
            for batch_num, batch in enumerate(batches, 1):
                print(f"\n📦 Processing Batch {batch_num}/{len(batches)} ({len(batch)} stocks)")
                
                batch_qualified = []
                
                for stock in batch:
                    try:
                        symbol = stock['symbol']
                        name = stock['name']
                        
                        print(f"   Analyzing {symbol}...")
                        
                        # Fetch weekly data
                        weekly_data = DataProvider.fetch_weekly_data(symbol, period="2y")
                        
                        if weekly_data.empty or len(weekly_data) < 20:
                            # Skip symbols with fewer than 20 weekly data points
                            scan_metadata['errors'].append(f"Insufficient data for {symbol} ({len(weekly_data)} weeks)")
                            continue
                        
                        # Perform technical analysis
                        analysis_result = TechnicalAnalysis.analyze_stock(symbol, weekly_data)
                        
                        if analysis_result:
                            scan_metadata['total_stocks_analyzed'] += 1
                            
                            # Add stock name and sector info
                            analysis_result['name'] = name
                            stock_info = DataProvider.get_stock_info(symbol)
                            analysis_result['sector'] = stock_info.get('sector', 'Unknown')
                            
                            # Check if stock meets minimum 2 criteria
                            if analysis_result['criteria_met'] >= 2:
                                analysis_result['qualified'] = True
                                batch_qualified.append(analysis_result)
                                print(f"   ✅ {symbol} QUALIFIED - {analysis_result['criteria_met']}/5 criteria ({analysis_result['setup_strength']})")
                            else:
                                print(f"   ❌ {symbol} - {analysis_result['criteria_met']}/5 criteria")
                        else:
                            scan_metadata['errors'].append(f"Analysis failed for {symbol}")
                    
                    except Exception as e:
                        error_msg = f"Error processing {symbol}: {str(e)}"
                        print(f"   ⚠️ {error_msg}")
                        scan_metadata['errors'].append(error_msg)
                        continue
                
                qualified_stocks.extend(batch_qualified)
                
                print(f"📈 Batch {batch_num} Results: {len(batch_qualified)} qualified stocks found")
                
                # Add small delay between batches to respect API limits
                if batch_num < len(batches) and batch_mode:
                    import time
                    time.sleep(2)  # 2-second delay between batches
            
            # Sort qualified stocks by criteria met (descending) then by risk-reward ratio
            qualified_stocks.sort(key=lambda x: (x['criteria_met'], x['risk_reward']), reverse=True)
            
            scan_metadata['qualified_stocks_found'] = len(qualified_stocks)
            self.scan_results = qualified_stocks
            self.last_scan_time = datetime.now()
            
            # Calculate scan duration
            end_time = datetime.now()
            duration = end_time - start_time
            scan_metadata['scan_duration_minutes'] = round(duration.total_seconds() / 60, 2)
            
            print(f"\n✅ COMPREHENSIVE SCAN COMPLETED!")
            print(f"⏱️ Total time: {scan_metadata['scan_duration_minutes']} minutes")
            print(f"📊 Analyzed: {scan_metadata['total_stocks_analyzed']} stocks")
            print(f"🎯 Qualified: {len(qualified_stocks)} stocks (2+ criteria)")
            
            # Show criteria distribution
            criteria_distribution = {}
            sector_distribution = {}
            
            for stock in qualified_stocks:
                criteria_count = stock['criteria_met']
                criteria_distribution[criteria_count] = criteria_distribution.get(criteria_count, 0) + 1
                
                sector = stock.get('sector', 'Unknown')
                sector_distribution[sector] = sector_distribution.get(sector, 0) + 1
            
            print(f"\n📋 Criteria Distribution:")
            for criteria_count in sorted(criteria_distribution.keys(), reverse=True):
                count = criteria_distribution[criteria_count]
                percentage = (count / len(qualified_stocks)) * 100
                print(f"   {criteria_count}/5 criteria: {count} stocks ({percentage:.1f}%)")
            
            print(f"\n🏢 Top Sectors with Qualified Stocks:")
            top_sectors = sorted(sector_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
            for sector, count in top_sectors:
                print(f"   {sector}: {count} stocks")
            
            return {
                'status': 'success',
                'scan_metadata': scan_metadata,
                'qualified_stocks': qualified_stocks,
                'total_qualified': len(qualified_stocks),
                'criteria_distribution': criteria_distribution,
                'sector_distribution': sector_distribution,
                'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
                'performance_stats': {
                    'total_universe': total_stocks,
                    'analyzed_percentage': round((scan_metadata['total_stocks_analyzed'] / total_stocks) * 100, 1),
                    'qualification_rate': round((len(qualified_stocks) / scan_metadata['total_stocks_analyzed']) * 100, 1) if scan_metadata['total_stocks_analyzed'] > 0 else 0
                }
            }
            
        except Exception as e:
            error_msg = f"Critical error in comprehensive scan: {str(e)}"
            print(error_msg)
            return {
                'status': 'error',
                'message': error_msg,
                'qualified_stocks': [],
                'total_qualified': 0
            }
        
        finally:
            self.scan_in_progress = False
    
    def run_quick_scan(self, sample_size: int = 100) -> Dict[str, Any]:
        """
        Run a quick scan on a sample of stocks for testing
        Args:
            sample_size: Number of stocks to scan (default 100)
        """
        print(f"🚀 Running quick scan on {sample_size} stocks...")
        
        # Get sample stocks
        all_stocks = DataProvider.get_stock_list()[:sample_size]
        
        # Temporarily replace the stock list for quick scan
        original_get_stock_list = DataProvider.get_stock_list
        DataProvider.get_stock_list = lambda: all_stocks
        
        try:
            result = self.run_daily_scan(batch_mode=True)
            result['scan_type'] = 'quick_scan'
            result['sample_size'] = sample_size
            return result
        finally:
            # Restore original method
            DataProvider.get_stock_list = original_get_stock_list
    
    def get_sector_wise_analysis(self) -> Dict[str, Any]:
        """Get analysis results grouped by sector"""
        if not self.scan_results:
            return {'message': 'No scan results available. Run a scan first.'}
        
        sector_analysis = {}
        
        for stock in self.scan_results:
            sector = stock.get('sector', 'Unknown')
            
            if sector not in sector_analysis:
                sector_analysis[sector] = {
                    'total_stocks': 0,
                    'average_criteria': 0,
                    'perfect_setups': 0,
                    'strong_setups': 0,
                    'stocks': []
                }
            
            sector_data = sector_analysis[sector]
            sector_data['total_stocks'] += 1
            sector_data['average_criteria'] += stock['criteria_met']
            
            if stock['criteria_met'] == 5:
                sector_data['perfect_setups'] += 1
            elif stock['criteria_met'] == 4:
                sector_data['strong_setups'] += 1
            
            sector_data['stocks'].append({
                'symbol': stock['symbol'],
                'name': stock['name'],
                'criteria_met': stock['criteria_met'],
                'setup_strength': stock['setup_strength'],
                'current_price': stock['current_price']
            })
        
        # Calculate averages
        for sector, data in sector_analysis.items():
            data['average_criteria'] = round(data['average_criteria'] / data['total_stocks'], 2)
        
        # Sort by total qualified stocks
        sorted_sectors = dict(sorted(sector_analysis.items(), key=lambda x: x[1]['total_stocks'], reverse=True))
        
        return {
            'total_sectors_with_qualified_stocks': len(sorted_sectors),
            'sector_analysis': sorted_sectors
        }
    
    def get_portfolio_recommendations(self) -> Dict[str, Any]:
        """
        Generate enhanced portfolio recommendations for Nifty 500+ universe
        Maximum 30 positions for broader diversification
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
        
        print(f"Portfolio Analysis for Nifty 500+ Universe:")
        print(f"  Perfect (5/5): {len(perfect_stocks)} stocks")
        print(f"  Strong (4/5): {len(strong_stocks)} stocks") 
        print(f"  Good (3/5): {len(good_stocks)} stocks")
        print(f"  Moderate (2/5): {len(moderate_stocks)} stocks")
        
        # Prioritize by strength and diversify across sectors
        prioritized_stocks = perfect_stocks + strong_stocks + good_stocks + moderate_stocks
        
        # Enhanced portfolio for larger universe - increase to 30 positions
        max_positions = 30
        selected_stocks = []
        sector_counts = {}
        max_per_sector = 4  # Limit per sector for diversification
        
        for stock in prioritized_stocks:
            if len(selected_stocks) >= max_positions:
                break
            
            sector = stock.get('sector', 'Unknown')
            sector_count = sector_counts.get(sector, 0)
            
            # Include stock if under sector limit or if it's a perfect setup
            if sector_count < max_per_sector or stock['criteria_met'] == 5:
                selected_stocks.append(stock)
                sector_counts[sector] = sector_count + 1
        
        portfolio_recommendations = []
        total_allocation = 0
        
        for i, stock in enumerate(selected_stocks, 1):
            # Refined allocation based on criteria strength
            if stock['criteria_met'] == 5:
                allocation = 4.0  # Perfect setups
                risk_category = "HIGHEST CONFIDENCE"
            elif stock['criteria_met'] == 4:
                allocation = 3.5  # Strong setups
                risk_category = "HIGH CONFIDENCE"
            elif stock['criteria_met'] == 3:
                allocation = 3.0  # Good setups
                risk_category = "MODERATE CONFIDENCE"
            else:  # 2 criteria
                allocation = 2.5  # Conservative setups
                risk_category = "CONSERVATIVE"
            
            total_allocation += allocation
            
            portfolio_recommendations.append({
                'rank': i,
                'symbol': stock['symbol'],
                'name': stock.get('name', stock['symbol']),
                'sector': stock.get('sector', 'Unknown'),
                'current_price': stock['current_price'],
                'allocation_percent': allocation,
                'stop_loss': stock['stop_loss'],
                'target': stock['target'],
                'risk_reward': stock['risk_reward'],
                'criteria_met': stock['criteria_met'],
                'setup_strength': stock['setup_strength'],
                'risk_category': risk_category,
                'entry_reason': f'Nifty 500+ qualified: {stock["criteria_met"]}/5 criteria ({stock["setup_strength"]} setup)'
            })
        
        # Get sector diversification stats
        sector_breakdown = {}
        for rec in portfolio_recommendations:
            sector = rec['sector']
            sector_breakdown[sector] = sector_breakdown.get(sector, 0) + 1
        
        return {
            'portfolio_size': len(portfolio_recommendations),
            'total_allocation': round(total_allocation, 1),
            'max_positions': max_positions,
            'recommendations': portfolio_recommendations,
            'universe_coverage': f"Nifty 500+ ({DataProvider.get_stock_count()} stocks)",
            'diversification': {
                'sectors_represented': len(sector_breakdown),
                'sector_breakdown': sector_breakdown,
                'max_per_sector_limit': max_per_sector
            },
            'criteria_breakdown': {
                'perfect_5_criteria': len(perfect_stocks),
                'strong_4_criteria': len(strong_stocks), 
                'good_3_criteria': len(good_stocks),
                'moderate_2_criteria': len(moderate_stocks),
                'total_universe_qualified': len(self.scan_results)
            },
            'risk_management': {
                'allocation_strategy': 'Sector-diversified weighted by criteria strength',
                'min_criteria_required': '2 out of 5 technical criteria',
                'universe_coverage': f'{DataProvider.get_stock_count()} Nifty 500+ stocks',
                'sector_limits': f'Maximum {max_per_sector} stocks per sector',
                'position_sizing': 'Variable allocation: 4%/3.5%/3%/2.5%',
                'rebalancing': 'Daily profit taking at 3%/6% gains'
            }
        }
    
    def get_scan_status(self) -> Dict[str, Any]:
        """Get enhanced scan status for Nifty 500+ system"""
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        # Get criteria and sector distribution from last scan
        criteria_stats = {'2_criteria': 0, '3_criteria': 0, '4_criteria': 0, '5_criteria': 0}
        sector_stats = {}
        
        if self.scan_results:
            for stock in self.scan_results:
                criteria_count = stock['criteria_met']
                if criteria_count >= 2:
                    criteria_stats[f'{criteria_count}_criteria'] = criteria_stats.get(f'{criteria_count}_criteria', 0) + 1
                
                sector = stock.get('sector', 'Unknown')
                sector_stats[sector] = sector_stats.get(sector, 0) + 1
        
        return {
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S IST'),
            'scan_in_progress': self.scan_in_progress,
            'last_scan_time': self.last_scan_time.strftime('%Y-%m-%d %H:%M:%S IST') if self.last_scan_time else 'Never',
            'universe_size': DataProvider.get_stock_count(),
            'universe_name': 'Nifty 500+ Comprehensive',
            'qualified_stocks_count': len(self.scan_results),
            'minimum_criteria_required': 2,
            'criteria_distribution': criteria_stats,
            'top_sectors': dict(sorted(sector_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
            'should_run_scan': self.should_run_daily_scan(),
            'market_hours': self.is_market_time(),
            'next_scan_time': '17:00 IST (Daily)',
            'scan_capabilities': {
                'batch_processing': True,
                'sector_analysis': True,
                'quick_scan_available': True,
                'comprehensive_coverage': True
            }
        }
    
    # Keep existing helper methods
    def is_market_time(self) -> bool:
        """Check if it's market hours (9:15 AM to 3:30 PM IST)"""
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_start <= now <= market_end
    
    def should_run_daily_scan(self) -> bool:
        """Check if daily scan should run"""
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        scan_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
        
        if now < scan_time:
            return False
        
        if self.last_scan_time:
            last_scan_date = self.last_scan_time.date()
            today = now.date()
            
            if last_scan_date >= today:
                return False
        
        return True
