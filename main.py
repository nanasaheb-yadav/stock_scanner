from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import asyncio
import json
from datetime import datetime
import os
import logging
from scanner import StockScanner  # This will now use the updated scanner
from data_provider import DataProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Stock Scanner", description="2+ Criteria Swing Trading Scanner")

# Initialize stock scanner
scanner = StockScanner()

# Global variable to store WebSocket connections
websocket_connections = []

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stock Scanner - 2+ Criteria System</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a1a1a; color: #ffffff; line-height: 1.6; }
            .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 15px; }
            .header h1 { font-size: 2.5em; margin-bottom: 10px; }
            .header p { font-size: 1.2em; opacity: 0.9; }
            .criteria-info { background: #2a2a2a; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #4CAF50; }
            .criteria-info h3 { color: #4CAF50; margin-bottom: 10px; }
            .controls { display: flex; justify-content: center; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }
            .btn { padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 1em; font-weight: 600; text-decoration: none; display: inline-block; transition: all 0.3s; }
            .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .btn-success { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; }
            .btn-info { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .btn:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.3); }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .stat-card { background: #2a2a2a; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #333; }
            .stat-number { font-size: 2em; font-weight: bold; color: #4CAF50; margin-bottom: 5px; }
            .stat-label { color: #aaa; font-size: 0.9em; }
            .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
            .status-success { background: #4CAF50; }
            .status-warning { background: #FF9800; }
            .status-error { background: #F44336; }
            .results-section { background: #2a2a2a; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
            .results-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            .results-table th, .results-table td { padding: 12px; text-align: left; border-bottom: 1px solid #444; }
            .results-table th { background: #333; color: #fff; font-weight: 600; }
            .results-table tr:hover { background: #333; }
            .qualified { color: #4CAF50; font-weight: bold; }
            .not-qualified { color: #F44336; }
            .loading { text-align: center; padding: 40px; }
            .spinner { border: 4px solid #333; border-top: 4px solid #667eea; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 20px; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .criteria-badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; margin: 2px; }
            .criteria-5 { background: #4CAF50; color: white; }
            .criteria-4 { background: #8BC34A; color: white; }
            .criteria-3 { background: #FF9800; color: white; }
            .criteria-2 { background: #FF5722; color: white; }
            .criteria-1 { background: #F44336; color: white; }
            .strength-badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; margin-left: 5px; }
            .strength-PERFECT { background: #4CAF50; color: white; }
            .strength-STRONG { background: #8BC34A; color: white; }
            .strength-GOOD { background: #FF9800; color: white; }
            .strength-MODERATE { background: #FF5722; color: white; }
            .log-section { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 15px; max-height: 300px; overflow-y: auto; font-family: monospace; font-size: 0.9em; }
            .footer { text-align: center; margin-top: 40px; padding: 20px; border-top: 1px solid #333; color: #aaa; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Stock Scanner Pro - Relaxed Mode</h1>
                <p>2+ Criteria Swing Trading System | Nifty 50 Analysis</p>
            </div>

            <div class="criteria-info">
                <h3>📋 Updated Scanning Criteria (Minimum 2 out of 5)</h3>
                <p><strong>Now Qualifying:</strong> Stocks meeting at least 2 technical criteria (instead of all 5)</p>
                <p><strong>Criteria Strength:</strong> PERFECT (5/5) → STRONG (4/5) → GOOD (3/5) → MODERATE (2/5)</p>
                <p><strong>Portfolio Allocation:</strong> Weighted by criteria strength (5% → 4% → 3% → 2%)</p>
            </div>

            <div class="controls">
                <button class="btn btn-primary" onclick="runScan()">▶️ Run Relaxed Scan</button>
                <button class="btn btn-success" onclick="getPortfolioRecommendations()">📊 Portfolio Recommendations</button>
                <button class="btn btn-info" onclick="refreshStatus()">🔄 Refresh Status</button>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="qualified-count">-</div>
                    <div class="stat-label">Qualified Stocks (2+)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="perfect-count">-</div>
                    <div class="stat-label">Perfect Setups (5/5)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="strong-count">-</div>
                    <div class="stat-label">Strong Setups (4/5)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="total-analyzed">-</div>
                    <div class="stat-label">Stocks Analyzed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="last-scan-time">-</div>
                    <div class="stat-label">Last Scan</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="scan-status">
                        <span class="status-indicator status-warning"></span>Ready
                    </div>
                    <div class="stat-label">System Status</div>
                </div>
            </div>

            <div class="results-section">
                <h2>📈 Qualified Stocks (2+ Criteria Matches)</h2>
                <div id="results-content">
                    <p style="text-align: center; color: #aaa; padding: 40px;">Click "Run Relaxed Scan" to start analyzing stocks...</p>
                </div>
            </div>

            <div class="results-section">
                <h2>📝 Scan Log</h2>
                <div class="log-section" id="scan-log">
                    <p>System ready. Updated to 2+ criteria qualification. Waiting for scan to start...</p>
                </div>
            </div>

            <div class="footer">
                <p>🔬 Technical Analysis: HMA (30/44) + MACD (3,21,9) + RSI (9) with Dual Crossover</p>
                <p>⚡ Updated: Now qualifies stocks with 2+ criteria (instead of all 5) | More opportunities!</p>
            </div>
        </div>

        <script>
            let scanInProgress = false;

            function addLog(message) {
                const logElement = document.getElementById('scan-log');
                const timestamp = new Date().toLocaleTimeString();
                logElement.innerHTML += `<br>[${timestamp}] ${message}`;
                logElement.scrollTop = logElement.scrollHeight;
            }

            function updateStats(data) {
                document.getElementById('qualified-count').textContent = data.total_qualified || 0;
                document.getElementById('total-analyzed').textContent = data.scan_metadata?.total_stocks_analyzed || 0;
                document.getElementById('last-scan-time').textContent = 
                    data.scan_metadata?.scan_time || 'Never';
                
                // Update criteria distribution stats
                if (data.criteria_distribution) {
                    document.getElementById('perfect-count').textContent = data.criteria_distribution[5] || 0;
                    document.getElementById('strong-count').textContent = data.criteria_distribution[4] || 0;
                }
            }

            function displayResults(qualifiedStocks) {
                const resultsContent = document.getElementById('results-content');
                
                if (!qualifiedStocks || qualifiedStocks.length === 0) {
                    resultsContent.innerHTML = '<p style="text-align: center; color: #aaa; padding: 40px;">No stocks meeting minimum 2 criteria found.</p>';
                    return;
                }

                let tableHTML = `
                    <table class="results-table">
                        <thead>
                            <tr>
                                <th>Stock</th>
                                <th>Price (₹)</th>
                                <th>Criteria</th>
                                <th>Setup Strength</th>
                                <th>HMA 30</th>
                                <th>HMA 44</th>
                                <th>Risk:Reward</th>
                                <th>Target</th>
                                <th>Stop Loss</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                qualifiedStocks.forEach(stock => {
                    const symbol = stock.symbol.replace('.NS', '');
                    const criteriaClass = `criteria-${stock.criteria_met}`;
                    const strengthClass = `strength-${stock.setup_strength}`;
                    
                    tableHTML += `
                        <tr>
                            <td><strong>${symbol}</strong><br><small>${stock.name || symbol}</small></td>
                            <td>₹${stock.current_price.toFixed(2)}</td>
                            <td><span class="criteria-badge ${criteriaClass}">${stock.criteria_met}/5</span></td>
                            <td><span class="strength-badge ${strengthClass}">${stock.setup_strength}</span></td>
                            <td>₹${stock.hma_30.toFixed(2)}</td>
                            <td>₹${stock.hma_44.toFixed(2)}</td>
                            <td>${stock.risk_reward.toFixed(2)}</td>
                            <td>₹${stock.target.toFixed(2)}</td>
                            <td>₹${stock.stop_loss.toFixed(2)}</td>
                            <td><span class="qualified">✅ QUALIFIED</span></td>
                        </tr>
                    `;
                });

                tableHTML += '</tbody></table>';
                resultsContent.innerHTML = tableHTML;
            }

            async function runScan() {
                if (scanInProgress) {
                    addLog('Scan already in progress...');
                    return;
                }

                scanInProgress = true;
                document.getElementById('scan-status').innerHTML = 
                    '<span class="status-indicator status-warning"></span>Scanning...';
                
                document.getElementById('results-content').innerHTML = `
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Analyzing Nifty 50 stocks with relaxed 2+ criteria... This may take 2-3 minutes.</p>
                    </div>
                `;

                addLog('Starting relaxed scan (2+ criteria required)...');

                try {
                    const response = await fetch('/api/scan', { method: 'POST' });
                    const data = await response.json();

                    if (data.status === 'success') {
                        addLog(`Relaxed scan completed! Found ${data.total_qualified} qualified stocks (2+ criteria).`);
                        
                        // Log criteria distribution
                        if (data.criteria_distribution) {
                            addLog(`Distribution: 5/5: ${data.criteria_distribution[5] || 0}, 4/5: ${data.criteria_distribution[4] || 0}, 3/5: ${data.criteria_distribution[3] || 0}, 2/5: ${data.criteria_distribution[2] || 0}`);
                        }
                        
                        updateStats(data);
                        displayResults(data.qualified_stocks);
                        
                        document.getElementById('scan-status').innerHTML = 
                            '<span class="status-indicator status-success"></span>Complete';
                    } else {
                        addLog(`Scan failed: ${data.message}`);
                        document.getElementById('scan-status').innerHTML = 
                            '<span class="status-indicator status-error"></span>Error';
                    }
                } catch (error) {
                    addLog(`Error: ${error.message}`);
                    document.getElementById('scan-status').innerHTML = 
                        '<span class="status-indicator status-error"></span>Error';
                } finally {
                    scanInProgress = false;
                }
            }

            async function refreshStatus() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    addLog(`Status updated. Minimum criteria: ${data.minimum_criteria_required}. Market hours: ${data.market_hours ? 'Yes' : 'No'}`);
                } catch (error) {
                    addLog(`Error getting status: ${error.message}`);
                }
            }

            async function getPortfolioRecommendations() {
                try {
                    const response = await fetch('/api/portfolio');
                    const data = await response.json();
                    
                    if (data.recommendations && data.recommendations.length > 0) {
                        addLog(`Portfolio generated with ${data.recommendations.length} positions.`);
                        addLog(`Breakdown: Perfect: ${data.criteria_breakdown?.perfect_5_criteria || 0}, Strong: ${data.criteria_breakdown?.strong_4_criteria || 0}, Good: ${data.criteria_breakdown?.good_3_criteria || 0}, Moderate: ${data.criteria_breakdown?.moderate_2_criteria || 0}`);
                        alert(`Portfolio recommendations generated with ${data.recommendations.length} stocks across different strength levels!`);
                    } else {
                        addLog('No portfolio recommendations available. Run a scan first.');
                        alert('Please run a scan first to get portfolio recommendations.');
                    }
                } catch (error) {
                    addLog(`Error getting portfolio: ${error.message}`);
                }
            }

            // Auto-refresh status every 30 seconds
            setInterval(refreshStatus, 30000);
            
            // Initial status load
            refreshStatus();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/scan")
async def run_scan():
    """Run the daily stock scan with relaxed 2+ criteria"""
    try:
        logger.info("Starting manual scan request with 2+ criteria")
        result = scanner.run_daily_scan()
        
        # Broadcast to WebSocket connections
        await broadcast_to_websockets({
            'type': 'scan_complete',
            'data': result
        })
        
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error in scan: {e}")
        return JSONResponse({
            'status': 'error',
            'message': str(e),
            'qualified_stocks': [],
            'total_qualified': 0
        })

@app.get("/api/status")
async def get_status():
    """Get current scanner status"""
    try:
        status = scanner.get_scan_status()
        return JSONResponse(status)
    except Exception as e:
        return JSONResponse({'error': str(e)})

@app.get("/api/portfolio")
async def get_portfolio_recommendations():
    """Get portfolio recommendations with weighted allocation"""
    try:
        recommendations = scanner.get_portfolio_recommendations()
        return JSONResponse(recommendations)
    except Exception as e:
        return JSONResponse({'error': str(e)})

@app.get("/api/stock/{symbol}")
async def get_stock_analysis(symbol: str):
    """Get detailed analysis for a specific stock"""
    try:
        # Add .NS if not present (for Yahoo Finance)
        if not symbol.endswith('.NS'):
            symbol += '.NS'
        
        analysis = scanner.get_stock_analysis(symbol)
        return JSONResponse(analysis)
    except Exception as e:
        return JSONResponse({'error': str(e)})

@app.get("/api/test")
async def test_connection():
    """Test if data provider is working"""
    try:
        is_working = DataProvider.test_connection()
        return JSONResponse({
            'status': 'success',
            'data_provider_working': is_working,
            'message': 'Data provider is working' if is_working else 'Data provider not responding'
        })
    except Exception as e:
        return JSONResponse({
            'status': 'error',
            'message': str(e)
        })

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(30)
            await websocket.send_json({
                'type': 'heartbeat',
                'timestamp': datetime.now().isoformat()
            })
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)

async def broadcast_to_websockets(message: dict):
    """Broadcast message to all connected WebSocket clients"""
    if websocket_connections:
        for websocket in websocket_connections.copy():
            try:
                await websocket.send_json(message)
            except:
                # Remove disconnected websocket
                if websocket in websocket_connections:
                    websocket_connections.remove(websocket)

@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("Stock Scanner starting up with 2+ criteria system...")
    
    # Test data provider connection
    try:
        if DataProvider.test_connection():
            logger.info("✅ Data provider connection successful")
        else:
            logger.warning("⚠️ Data provider connection failed")
    except Exception as e:
        logger.error(f"❌ Data provider test failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Stock Scanner shutting down...")

if __name__ == "__main__":
    # Get port from environment variable (for deployment) or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Set to True for development
        log_level="info"
    )
