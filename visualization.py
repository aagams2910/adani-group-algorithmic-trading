import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict
from strategies import TradeSignal
import numpy as np

class ChartManager:
    def __init__(self):
        self.colors = {
            'long': '#00ff00',
            'short': '#ff0000',
            'profit': '#00ff00',
            'loss': '#ff0000',
            'neutral': '#808080'
        }
    
    def create_price_chart(self, data: pd.DataFrame, signals: List[TradeSignal], title: str) -> go.Figure:
        """Create a candlestick chart with technical indicators and signals"""
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2]
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                name='Price'
            ),
            row=1, col=1
        )
        
        # Add Bollinger Bands
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['BB_Upper'],
                name='BB Upper',
                line=dict(color='rgba(250, 0, 0, 0.3)')
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['BB_Lower'],
                name='BB Lower',
                line=dict(color='rgba(0, 250, 0, 0.3)')
            ),
            row=1, col=1
        )
        
        # Add moving averages
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['EMA_20'],
                name='EMA 20',
                line=dict(color='blue')
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['EMA_50'],
                name='EMA 50',
                line=dict(color='orange')
            ),
            row=1, col=1
        )
        
        # Add RSI
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['RSI'],
                name='RSI',
                line=dict(color='purple')
            ),
            row=2, col=1
        )
        
        # Add RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        # Add MACD
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['MACD'],
                name='MACD',
                line=dict(color='blue')
            ),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['MACD_Signal'],
                name='Signal',
                line=dict(color='orange')
            ),
            row=3, col=1
        )
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data['MACD_Hist'],
                name='Histogram',
                marker_color='gray'
            ),
            row=3, col=1
        )
        
        # Add signals with legend control
        long_signal_plotted = False
        short_signal_plotted = False
        
        for signal in signals:
            color = self.colors['long'] if signal.type == 'LONG' else self.colors['short']
            show_legend = False
            
            if signal.type == 'LONG' and not long_signal_plotted:
                show_legend = True
                long_signal_plotted = True
            elif signal.type == 'SHORT' and not short_signal_plotted:
                show_legend = True
                short_signal_plotted = True
            
            fig.add_trace(
                go.Scatter(
                    x=[signal.timestamp],
                    y=[signal.price],
                    mode='markers',
                    marker=dict(
                        symbol='triangle-up' if signal.type == 'LONG' else 'triangle-down',
                        size=15,
                        color=color
                    ),
                    name=f'{signal.type} Signal',
                    text=signal.reason,
                    showlegend=show_legend
                ),
                row=1, col=1
            )
        
        # Update layout
        fig.update_layout(
            title=title,
            xaxis_rangeslider_visible=False,
            height=800,
            showlegend=True
        )
        
        return fig
    
    def create_performance_chart(self, returns: pd.Series, title: str) -> go.Figure:
        """Create a performance chart showing cumulative returns"""
        cumulative_returns = (1 + returns).cumprod()
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=cumulative_returns.index,
                y=cumulative_returns,
                name='Cumulative Returns',
                line=dict(color='blue')
            )
        )
        
        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Cumulative Returns',
            height=400,
            showlegend=True
        )
        
        return fig
    
    def create_drawdown_chart(self, returns: pd.Series, title: str) -> go.Figure:
        """Create a drawdown chart"""
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns / running_max - 1) * 100
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown,
                name='Drawdown %',
                line=dict(color='red')
            )
        )
        
        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Drawdown %',
            height=400,
            showlegend=True
        )
        
        return fig
    
    def create_metrics_table(self, returns: pd.Series) -> pd.DataFrame:
        """Create a table of performance metrics"""
        metrics = {
            'Total Return (%)': (returns.sum() * 100).round(2),
            'Annualized Return (%)': ((1 + returns.mean()) ** 252 - 1) * 100,
            'Sharpe Ratio': (returns.mean() / returns.std() * np.sqrt(252)).round(2),
            'Max Drawdown (%)': ((returns.cumsum() - returns.cumsum().cummax()).min() * 100).round(2),
            'Win Rate (%)': (returns > 0).mean() * 100,
            'Average Win (%)': returns[returns > 0].mean() * 100,
            'Average Loss (%)': returns[returns < 0].mean() * 100,
            'Profit Factor': abs(returns[returns > 0].sum() / returns[returns < 0].sum()).round(2)
        }
        
        return pd.DataFrame(list(metrics.items()), columns=['Metric', 'Value']) 