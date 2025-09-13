# Complete Stock Scanner - Single Python Project

## Project Overview
A complete stock market scanner implementing Nitin Hulaji's 5-criteria swing trading methodology. Scans Nifty 50 stocks daily at 5 PM IST using free data sources.

## Features
- Daily automated scanning at 5 PM IST
- 5-criteria technical analysis (HMA, MACD, RSI)
- Web-based dashboard
- Real-time portfolio tracking
- Free deployment ready

## Quick Start
1. Download all project files
2. Deploy to Railway.app (free hosting)
3. Access your live scanner at the provided URL

## Files Structure
```
stock-scanner/
├── main.py              # FastAPI web server
├── technical_analysis.py # Technical indicators
├── data_provider.py     # Data fetching (Yahoo Finance)
├── scanner.py           # Scanning logic
├── requirements.txt     # Dependencies
├── static/
│   ├── index.html       # Web interface
│   ├── style.css        # Styling
│   └── script.js        # Frontend JavaScript
├── README.md            # This file
└── railway.json         # Deployment config
```

## Technical Criteria
1. **HMA Filter**: 30-period and 44-period Hull Moving Average
2. **Price Position**: Stock between 30 HMA and 44 HMA
3. **MACD Setup**: Custom (3,21,9) with 8+ histogram bars
4. **RSI Trigger**: 9-period RSI with dual crossover
5. **Weekly Timeframe**: All analysis on weekly data

## Deployment Instructions

### Option 1: Railway.app (Recommended - FREE)
1. Go to railway.app and sign up
2. Connect your GitHub account
3. Upload project files to GitHub repository
4. Deploy directly from GitHub
5. Railway provides HTTPS URL automatically

### Option 2: Render.com (Alternative - FREE)
1. Sign up at render.com
2. Create new web service
3. Connect GitHub repository
4. Deploy with one click

### Local Development
```bash
pip install -r requirements.txt
python main.py
# Open http://localhost:8000
```

## Cost: 100% FREE
- Data: Yahoo Finance API (free)
- Hosting: Railway.app free tier
- Domain: railway.app subdomain
- No credit card required

## Support
For issues, check the logs in your hosting dashboard.