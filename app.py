import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from pathlib import Path
from data_manager import DataManager
from strategies import (
    ACCStrategy,
    AdaniEnterprisesStrategy,
    AdaniPowerStrategy,
    AdaniPortsStrategy
)
from visualization import ChartManager
from portfolio_analysis import PortfolioAnalyzer

# Set page configuration
st.set_page_config(
    page_title="Adani Group Trading Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize managers
data_manager = DataManager()
chart_manager = ChartManager()

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and description
st.title("Adani Group Trading Dashboard")
st.markdown("""
    This dashboard implements four distinct swing trading strategies for Adani Group stocks:
    - ACC Limited: Mean Reversion with Momentum Filter
    - Adani Enterprises: Breakout Momentum
    - Adani Power: Sector Rotation with Technical Confirmation
    - Adani Ports: Infrastructure Play with Momentum
""")

# Sidebar configuration
st.sidebar.title("Strategy Configuration")

# Date range selector
st.sidebar.subheader("Date Range")
start_date = st.sidebar.date_input(
    "Start Date",
    datetime.date(2015, 2, 2)
)
end_date = st.sidebar.date_input(
    "End Date",
    datetime.date(2019, 5, 15)
)

# Stock selection
st.sidebar.subheader("Stock Selection")
selected_stock = st.sidebar.selectbox(
    "Select Stock",
    ["ACC", "Adani Enterprises", "Adani Power", "Adani Ports", "Portfolio Analysis"]
)

if selected_stock == "Portfolio Analysis":
    st.markdown("### Portfolio Analysis")
    
    # Calculate returns for all stocks
    stock_returns = {}
    strategies = {
        "ACC": ACCStrategy,
        "Adani Enterprises": AdaniEnterprisesStrategy,
        "Adani Power": AdaniPowerStrategy,
        "Adani Ports": AdaniPortsStrategy
    }
    
    # Create tabs for portfolio analysis
    tab1, tab2 = st.tabs(["Portfolio Overview", "Individual Stocks"])
    
    with tab1:
        # Calculate portfolio metrics
        for stock_name, strategy_class in strategies.items():
            stock_data = data_manager.get_stock_data(
                stock_name,
                start_date=start_date,
                end_date=end_date
            )
            strategy = strategy_class(stock_data)
            signals = strategy.generate_signals()
            returns = strategy.calculate_returns()
            stock_returns[stock_name] = returns
        
        # Create portfolio analyzer
        portfolio = PortfolioAnalyzer(stock_returns)
        portfolio.display_portfolio_metrics()
    
    with tab2:
        # Display individual stock metrics
        st.subheader("Individual Stock Performance")
        for stock_name, strategy_class in strategies.items():
            with st.expander(f"{stock_name} Performance"):
                stock_data = data_manager.get_stock_data(
                    stock_name,
                    start_date=start_date,
                    end_date=end_date
                )
                strategy = strategy_class(stock_data)
                signals = strategy.generate_signals()
                returns = strategy.calculate_returns()
                
                # Display metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(
                        chart_manager.create_performance_chart(
                            returns,
                            f"{stock_name} Performance"
                        ),
                        use_container_width=True
                    )
                with col2:
                    st.plotly_chart(
                        chart_manager.create_drawdown_chart(
                            returns,
                            f"{stock_name} Drawdown Analysis"
                        ),
                        use_container_width=True
                    )
                
                # Display signals
                if signals:
                    signals_data = []
                    for signal in signals:
                        signals_data.append({
                            'Date': signal.timestamp,
                            'Type': signal.type,
                            'Price': signal.price,
                            'Stop Loss': signal.stop_loss,
                            'Take Profit': signal.take_profit,
                            'Reason': signal.reason
                        })
                    signals_df = pd.DataFrame(signals_data)
                    st.dataframe(signals_df, use_container_width=True)
                else:
                    st.info("No signals generated for the selected period.")

else:
    # Get data for selected stock
    stock_data = data_manager.get_stock_data(
        selected_stock,
        start_date=start_date,
        end_date=end_date
    )

    # Initialize strategy based on selected stock
    if selected_stock == "ACC":
        strategy = ACCStrategy(stock_data)
        st.markdown("### ACC Limited - Mean Reversion with Momentum Filter Strategy")
    elif selected_stock == "Adani Enterprises":
        strategy = AdaniEnterprisesStrategy(stock_data)
        st.markdown("### Adani Enterprises - Breakout Momentum Strategy")
    elif selected_stock == "Adani Power":
        strategy = AdaniPowerStrategy(stock_data)
        st.markdown("### Adani Power - Sector Rotation with Technical Confirmation Strategy")
    elif selected_stock == "Adani Ports":
        strategy = AdaniPortsStrategy(stock_data)
        st.markdown("### Adani Ports - Infrastructure Play with Momentum Strategy")

    # Generate signals
    signals = strategy.generate_signals()
    returns = strategy.calculate_returns()

    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Price Analysis", "Performance Metrics", "Trade Signals"])

    with tab1:
        # Price chart with indicators
        st.plotly_chart(
            chart_manager.create_price_chart(
                stock_data,
                signals,
                f"{selected_stock} Price Analysis"
            ),
            use_container_width=True
        )

    with tab2:
        # Performance metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(
                chart_manager.create_performance_chart(
                    returns,
                    f"{selected_stock} Performance"
                ),
                use_container_width=True
            )
        
        with col2:
            st.plotly_chart(
                chart_manager.create_drawdown_chart(
                    returns,
                    f"{selected_stock} Drawdown Analysis"
                ),
                use_container_width=True
            )
        
        # Metrics table
        metrics_df = chart_manager.create_metrics_table(returns)
        st.dataframe(metrics_df, use_container_width=True)

    with tab3:
        # Trade signals table
        if signals:
            signals_data = []
            for signal in signals:
                signals_data.append({
                    'Date': signal.timestamp,
                    'Type': signal.type,
                    'Price': signal.price,
                    'Stop Loss': signal.stop_loss,
                    'Take Profit': signal.take_profit,
                    'Reason': signal.reason
                })
            
            signals_df = pd.DataFrame(signals_data)
            st.dataframe(signals_df, use_container_width=True)
        else:
            st.info("No signals generated for the selected period.")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit • Data from 2015-2019") 