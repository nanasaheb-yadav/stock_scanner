# 🚀 Complete Stock Scanner - Deployment Guide

## 📋 What You're Getting

A complete, working stock market scanner that:
- ✅ Analyzes Nifty 50 stocks using real Yahoo Finance data
- ✅ Implements all 5 technical criteria (HMA, MACD, RSI)
- ✅ Runs daily scans at 5 PM IST automatically
- ✅ Has a beautiful web dashboard
- ✅ Works 100% FREE on Railway.app hosting
- ✅ No API keys or credit cards needed

## 🎯 Step-by-Step Deployment (For Beginners)

### Step 1: Download All Files
Create a new folder on your computer called `stock-scanner` and save these files:

```
stock-scanner/
├── main.py                 ✅ Created
├── technical_analysis.py   ✅ Created  
├── data_provider.py        ✅ Created
├── scanner.py              ✅ Created
├── requirements.txt        ✅ Created
├── railway.json            ✅ Created
└── README.md               ✅ Created
```

### Step 2: Create GitHub Account & Repository
1. Go to [github.com](https://github.com) and create a free account
2. Click "New Repository" 
3. Name it `stock-scanner`
4. Make it Public
5. Click "Create Repository"

### Step 3: Upload Files to GitHub
**Option A: Using GitHub Website (Easiest)**
1. Click "uploading an existing file"
2. Drag and drop all 7 files into the upload area
3. Scroll down and click "Commit changes"

**Option B: Using Git Commands (If you know Git)**
```bash
git clone your-repo-url
cd stock-scanner
# Copy all files here
git add .
git commit -m "Initial stock scanner"
git push origin main
```

### Step 4: Deploy to Railway.app (100% FREE)
1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Sign up with your GitHub account
4. Click "Deploy from GitHub repo"
5. Select your `stock-scanner` repository
6. Click "Deploy Now"

**That's it! Railway will:**
- ✅ Automatically install Python and dependencies
- ✅ Start your application  
- ✅ Give you a live URL like: `https://stock-scanner-production.up.railway.app`

### Step 5: Access Your Live Scanner
1. Railway will show you the deployment URL
2. Click it to open your live stock scanner
3. Click "Run Scan Now" to test it

## 🛠️ How to Use Your Scanner

### Daily Scanning
1. **Automatic**: Runs daily at 5 PM IST
2. **Manual**: Click "Run Scan Now" anytime
3. **Results**: See qualified stocks meeting all 5 criteria

### Understanding Results
- **Green ✅**: Stock meets all 5 criteria (BUY signal)
- **Criteria Count**: 5/5 means perfect setup
- **Risk:Reward**: Higher is better (aim for 2.0+)
- **Stop Loss**: Exit if price goes below this
- **Target**: Profit booking level

### Portfolio Recommendations
- Click "Portfolio Recommendations" for position sizing
- Maximum 20 stocks, 5% allocation each
- Automatic risk management built-in

## 🔧 Troubleshooting

### If Deployment Fails:
1. Check all files are uploaded to GitHub
2. Make sure `requirements.txt` is present
3. Check Railway logs for error messages
4. Try redeploying from Railway dashboard

### If No Data Shows:
1. Click "Run Scan Now" first
2. Wait 2-3 minutes for scan to complete
3. Check if Yahoo Finance is accessible from your location
4. Try refreshing the page

### If Scans Are Slow:
- Normal: Takes 2-3 minutes to scan 47 stocks
- Yahoo Finance has rate limits (free service)
- Consider upgrading to paid data provider for faster scans

## 💰 Cost Breakdown

### Completely FREE Setup:
- **Data Source**: Yahoo Finance API (Free)
- **Hosting**: Railway.app free tier (500 hours/month)
- **Domain**: Railway provides HTTPS subdomain
- **Storage**: Included in free tier
- **Total Monthly Cost**: ₹0 (100% FREE)

### Optional Upgrades Later:
- **Custom Domain**: ₹800/year
- **Premium Data**: ₹2,000-4,000/month
- **Paid Hosting**: ₹1,500-3,000/month for faster performance

## 🎨 Customization Options

### Change Stock Universe:
Edit `data_provider.py` to add more stocks:
```python
# Add your stocks to NIFTY_50_STOCKS dictionary
'YOURSTOCK.NS': 'Your Stock Name'
```

### Modify Technical Parameters:
Edit `technical_analysis.py`:
- HMA periods (30, 44)
- MACD settings (3, 21, 9)  
- RSI periods (9, 3, 21)

### Change Scan Timing:
Edit `scanner.py`:
```python
# Change from 17:00 (5 PM) to your preferred time
scan_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
```

## 📊 What the Scanner Does

### Technical Analysis:
1. **HMA Filter**: Identifies trend direction using Hull Moving Average
2. **MACD Setup**: Confirms momentum with custom (3,21,9) settings  
3. **RSI Signals**: Detects strength with 9-period RSI dual crossover
4. **Price Position**: Ensures optimal entry between HMA levels
5. **Weekly Timeframe**: Reduces noise, focuses on significant moves

### Risk Management:
- Position sizing: 5% max per stock
- Stop losses: Below previous swing lows
- Targets: Based on swing highs
- Portfolio limit: 20 positions maximum

## 🚨 Important Notes

### Legal Disclaimer:
- This is for educational purposes
- Not financial advice
- Past performance doesn't guarantee future results
- Always do your own research before trading

### Data Limitations:
- Yahoo Finance data may have 15-20 minute delay
- Free tier has rate limits
- Some stocks may have data gaps
- Consider paid data for professional use

### Regulatory Compliance:
- Ensure compliance with local trading regulations
- Maintain proper risk management
- Keep detailed trading records
- Consult financial advisors for large investments

## 🆘 Support & Help

### If You Get Stuck:
1. **Check Railway Logs**: Look for error messages in Railway dashboard
2. **GitHub Issues**: Common problems and solutions
3. **Restart Deployment**: Sometimes fixes temporary issues
4. **Check File Structure**: Ensure all files are in root directory

### Common Issues:
- **Port Error**: Railway automatically sets PORT environment variable
- **Import Errors**: Check all files are uploaded correctly  
- **Data Errors**: Yahoo Finance occasionally has outages
- **Memory Errors**: Free tier has memory limits (restart deployment)

### Getting Updates:
- Download new versions of files and re-upload to GitHub
- Railway will automatically redeploy when you push changes
- Keep your requirements.txt updated

## 🎉 Congratulations!

You now have a professional-grade stock scanner running for FREE! 

Your scanner will:
- ✅ Analyze 47 Nifty stocks automatically
- ✅ Find high-probability swing trading setups  
- ✅ Provide risk-managed entry/exit levels
- ✅ Run 24/7 on Railway's cloud infrastructure
- ✅ Give you a competitive edge in the markets

**Start with small positions, test the signals, and gradually increase exposure as you gain confidence!**

---

*Built with ❤️ for Indian stock traders. Happy trading! 🚀*