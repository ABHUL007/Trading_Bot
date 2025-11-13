# 💼 Khusi Investment Model

Long-term investment prediction model for NIFTY 50.

## 📁 Files

- **Khusi_Invest_Model.py** - Main investment model
- **enhanced_khusi_10year.py** - Enhanced 10-year analysis
- **enhanced_khusi_10year.pkl** - Trained 10-year model
- **khusi_model_daily.pkl** - Daily prediction model

## 🎯 Purpose

This is a **long-term investment model** for NIFTY 50 predictions, separate from the automated trading system.

## 🚀 Usage

Run the model:
```powershell
conda run -p "../.conda" python Khusi_Invest_Model.py
```

## 📊 Model Details

- **Type:** Machine Learning based investment predictions
- **Timeframe:** Long-term (daily/10-year analysis)
- **Target:** NIFTY 50 investment signals
- **Not for:** Intraday trading (use Trading_System for that)

## 💾 Data Requirements

Uses historical NIFTY data from:
- `../NIFTY_1day_data.db` - Daily candles
- `../Nifty 50 Historical Data (1).csv` - Historical CSV data

## 📝 Notes

This model is independent from the trading system. It provides long-term investment insights, while the Trading System handles automated intraday options trading.
