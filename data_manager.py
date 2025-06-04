import pandas as pd
import numpy as np
import pandas_ta as ta
from pathlib import Path
from typing import Dict, List, Tuple

class DataManager:
    def __init__(self, data_dir: str = "csv_data"):
        self.data_dir = Path(data_dir)
        self.stock_data: Dict[str, pd.DataFrame] = {}
        self.load_all_data()
    
    def load_all_data(self):
        """Load all stock data from CSV files"""
        stock_files = {
            "ACC": "ACC-15minute",
            "Adani Enterprises": "ADANIENT-15minute",
            "Adani Power": "ADANIPOWER-15minute",
            "Adani Ports": "ADANIPORTS-15minute"
        }
        
        for stock_name, file_name in stock_files.items():
            file_path = self.data_dir / file_name
            if file_path.exists():
                df = pd.read_csv(file_path)
                # Convert column names to lowercase for consistency
                df.columns = df.columns.str.lower()
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                self.stock_data[stock_name] = df
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators for a given dataframe"""
        # RSI
        df['RSI'] = df.ta.rsi(length=14)
        
        # MACD
        macd = df.ta.macd(fast=12, slow=26, signal=9)
        df['MACD'] = macd['MACD_12_26_9']
        df['MACD_Signal'] = macd['MACDs_12_26_9']
        df['MACD_Hist'] = macd['MACDh_12_26_9']
        
        # Bollinger Bands
        bbands = df.ta.bbands(length=20, std=2)
        df['BB_Upper'] = bbands['BBU_20_2.0']
        df['BB_Middle'] = bbands['BBM_20_2.0']
        df['BB_Lower'] = bbands['BBL_20_2.0']
        
        # ADX and Directional Movement
        adx = df.ta.adx(length=14)
        df['ADX'] = adx['ADX_14']
        df['Plus_DI'] = adx['DMP_14']
        df['Minus_DI'] = adx['DMN_14']
        
        # ATR
        df['ATR'] = df.ta.atr(length=14)
        
        # Moving Averages
        df['SMA_20'] = df.ta.sma(length=20)
        df['SMA_50'] = df.ta.sma(length=50)
        df['SMA_100'] = df.ta.sma(length=100)
        df['EMA_20'] = df.ta.ema(length=20)
        df['EMA_50'] = df.ta.ema(length=50)
        df['EMA_100'] = df.ta.ema(length=100)
        
        # Volume Indicators
        df['Volume_SMA_20'] = df.ta.sma(length=20, close=df['volume'])
        df['Volume_Ratio'] = df['volume'] / df['Volume_SMA_20']
        
        # Rate of Change
        df['ROC_20'] = df.ta.roc(length=20)
        
        return df
    
    def get_stock_data(self, stock_name: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get processed stock data with technical indicators"""
        if stock_name not in self.stock_data:
            raise ValueError(f"Stock {stock_name} not found in data")
        
        df = self.stock_data[stock_name].copy()
        
        # Ensure date filtering is timezone-consistent
        tz = df.index.tz
        if start_date:
            start = pd.to_datetime(start_date)
            if tz is not None and start.tzinfo is None:
                start = start.tz_localize(tz)
            df = df[df.index >= start]
        if end_date:
            end = pd.to_datetime(end_date)
            if tz is not None and end.tzinfo is None:
                end = end.tz_localize(tz)
            df = df[df.index <= end]
        
        return self.calculate_technical_indicators(df)
    
    def get_relative_strength(self, stock_name: str, benchmark_name: str, period: int = 20) -> pd.Series:
        """Calculate relative strength between stock and benchmark"""
        stock_data = self.get_stock_data(stock_name)
        benchmark_data = self.get_stock_data(benchmark_name)
        
        stock_returns = stock_data['close'].pct_change(period)
        benchmark_returns = benchmark_data['close'].pct_change(period)
        
        return stock_returns - benchmark_returns 