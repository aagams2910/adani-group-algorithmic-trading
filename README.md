# Adani Group Trading Dashboard

A comprehensive Streamlit dashboard for implementing and analyzing swing trading strategies for Adani Group stocks.

## Features

- Interactive dashboard for analyzing four distinct trading strategies
- Real-time technical indicator calculations
- Performance metrics and visualization
- Trade signal generation and analysis
- Historical data analysis from 2015-2019

## Implemented Strategies

1. **ACC Limited - Mean Reversion with Momentum Filter**
   - RSI-based mean reversion
   - Bollinger Bands for volatility
   - MACD for momentum confirmation
   - Volume analysis for confirmation

2. **Adani Enterprises - Breakout Momentum**
   - Price breakout detection
   - Volume confirmation
   - ADX for trend strength
   - ATR for volatility analysis

3. **Adani Power - Sector Rotation**
   - Sector relative strength analysis
   - Technical confirmation with moving averages
   - Volume pattern analysis
   - RSI for entry/exit timing

4. **Adani Ports - Infrastructure Play**
   - Momentum-based strategy
   - Moving average alignment
   - Volume confirmation
   - Price action analysis

## Installation

1. Clone the repository:
```bash
git clone https://github.com/aagams2910/adani-group-algorithmic-trading.git
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Run the dashboard:
```bash
streamlit run app.py
```

## Data Structure

The dashboard uses 15-minute historical data for the following stocks:
- ACC Limited
- Adani Enterprises
- Adani Power
- Adani Ports

Data is stored in the `csv_data` directory with the following format:
- Date
- Open
- High
- Low
- Close
- Volume

## Technical Indicators

The dashboard calculates and displays:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- ADX (Average Directional Index)
- Moving Averages (SMA, EMA)
- Volume Indicators
- ATR (Average True Range)

## Performance Metrics

The dashboard provides comprehensive performance analysis:
- Total Return
- Annualized Return
- Sharpe Ratio
- Maximum Drawdown
- Win Rate
- Average Win/Loss
- Profit Factor
