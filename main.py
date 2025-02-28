"""
Stock Screener by adapting Mark Minervini's Trend Rules.

# Moving Averages (MA) Criteria:
1. The current stock price is above the 50-day (10 weeks), 150-day (30 weeks), and 200-day (40 weeks) SMA price lines.
2. The 200-day MA line is trending up for at least 1 month (ideally 4-5 months minimum in most cases).
3. The 50-day (10 weeks) MA is above both the 150-day and 200-day MAs.
4. The 150-day MA is above the 200-day MA.

# 52-Week Price Trends
5. Price within 25% of 52-week high but at least 30% above 52-week low.
````
# Fundamentals
6. (TODO) The Piotroski score is a financial tool that assesses a company's financial health and potential as an investment. 
   It's calculated using nine criteria, each worth one point if met. The score ranges from 0 to 9, with higher scores indicating better financial health.
   
(TODO)
Calculate change
Calculate spread
Implement some type of scoring system to rank the stocks
"""

from pandas import DataFrame
import yfinance as yf
import datetime as dt
import pandas as pd
import streamlit as st

# Constants for historical data retrieval
START = dt.datetime(2020, 1, 1)  # Start date for fetching stock data
END = dt.datetime.now()  # End date (current date)

def load_ticker_data(ticker: str = "") -> DataFrame:
    """
    Downloads historical stock data from Yahoo Finance and processes moving averages (MAs).
    
    Args:
        ticker (str): Stock ticker symbol.
    
    Returns:
        DataFrame: Downloaded and processed stock data.

    Raises:
        Exception: If no ticker is provided.
    """
    def _process_ticker(df: DataFrame) -> DataFrame:
        """
        Adds moving average (MA) calculations and trend indicators to the stock data.

        Args:
            df (DataFrame): Raw stock data.

        Returns:
            DataFrame: Processed data with additional MA and trend columns.
        """
        # Calculate moving averages
        lst_sma = [50, 150, 200]
        for sma in lst_sma:
            df[f'{str(sma)}MA'] = df['Close'].rolling(window=sma).mean()
        
        # Calculate 200-day MA trend over different time frames
        df['200MA_TREND'] = 0  # Initialize column to store trend count
        cnt = 0  
        prev_200ma = None  

        for idx, row in df.iterrows():
            curr_200ma = row['200MA']
            
            if prev_200ma is not None and curr_200ma > prev_200ma:
                cnt += 1  
            else:
                cnt = 0  
            
            df.at[idx, '200MA_TREND'] = cnt  
            prev_200ma = curr_200ma  

        # Trend indicators for different time periods
        df['200MA_TREND_1M'] = df['200MA_TREND'] >= 30
        df['200MA_TREND_3M'] = df['200MA_TREND'] >= 90
        df['200MA_TREND_6M'] = df['200MA_TREND'] >= 180
        
        # Check if 50-day MA is above both 150-day and 200-day MAs
        df['50MA>>'] = (df['50MA'] > df['150MA']) & (df['50MA'] > df['150MA'])
        
        # Check if 150-day MA is above 200-day MA
        df['150MA>200MA'] = df['150MA'] > df['200MA']

        # 52-Week High/Low Trend
        df['52WK_TREND'] = ((df['Close'] < df['Close'].rolling(window=52*7).max() * 1.25) | 
                     (df['Close'] > df['Close'].rolling(window=52*7).max() * 0.75)) & \
                    (df['Close'] > df['Close'].rolling(window=52*7).min() * 1.3)        

        return df
        
    if ticker:
        # Download historical stock data
        df_ticker = yf.download(ticker, START, END, group_by='ticker')
        df_ticker.columns = [col[1].strip() if isinstance(col, tuple) else col for col in df_ticker.columns]

        # Process moving averages and trends
        df_ticker = _process_ticker(df_ticker)
        
        return df_ticker
    else:
        raise Exception("No ticker defined.")
    
def check_conditions(df: DataFrame, conditions: list[str] = [
                        "200MA_TREND_1M",
                        "200MA_TREND_3M",
                        "200MA_TREND_6M",
                        "50MA>>",
                        "150MA>200MA",
                        "52WK_TREND"
                    ]) -> bool:
    """
    Checks if a stock meets predefined trend conditions.

    Args:
        df (DataFrame): Processed stock data.
        conditions (list[str]): List of column names representing the conditions.

    Returns:
        bool: True if the stock meets all conditions, otherwise False.
    """
    for condition in conditions:
        if df.iloc[-1][condition] == False:
            return False
    return True

def run() -> None:
    """
    Executes the stock screener process based on Minervini's rules:
    1. Reads the list of stock tickers from user input.
    2. Loads historical stock data for each ticker.
    3. Checks if the stock meets predefined trend conditions.
    4. Displays the screened stock data in a DataFrame.
    """
    
    # Streamlit UI Title
    st.title("Stock Screener using Minervini's Rules")
    
    # User input for stock tickers
    stock_list = st.text_input("Enter stock tickers separated by commas and space.")
    
    if stock_list:
        stock_list = stock_list.split(", ")  # Convert input string to a list of tickers
        
        if st.button("Run Screener"):
            
            print(f"Screening {len(stock_list)} stocks...")
            
            # Create an empty DataFrame to store the filtered stocks
            df_export = DataFrame(columns=[
                "Ticker", "Date", "Open", "High", "Low", "Close", "Volume", 
                "50MA", "150MA", "200MA", "200MA_TREND", 
                "200MA_TREND_1M", "200MA_TREND_3M", "200MA_TREND_6M", 
                "50MA>>", "150MA>200MA", "52WK_TREND"
            ])
            
            for stock in stock_list:
                print(f"Processing: {stock}")
                
                # Load historical stock data
                tmp_df = load_ticker_data(stock)
                
                # Check if the stock meets the trend conditions
                if not tmp_df.empty and check_conditions(tmp_df):
                    last_row_df = tmp_df.iloc[[-1]].copy()  # Extract the last row as DataFrame
                    last_row_df.insert(0, "Ticker", stock)  # Add the ticker symbol column
                    
                    # Append the row to the final export DataFrame
                    df_export = pd.concat([df_export, last_row_df], ignore_index=True)
            
            # Display the final screened stock data
            if df_export.empty:
                st.write("No Suitable Tickers")
            else:
                st.dataframe(df_export)
            
            
            
if __name__ == '__main__':
    run()
