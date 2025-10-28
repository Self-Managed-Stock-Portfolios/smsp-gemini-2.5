import pandas as pd
import os
from datetime import datetime

def update_portfolio(date_input: str) -> None:
    """Updates portfolio CSV for the given date using stored OHLCV data 
    from Stock Files/<date>.csv instead of fetching from NSE.
    
    - Current Price, Total Amount, and Perct Change are updated
      strictly with the Close price of the input date.
    - If a holding is not present in Stock Files data, row is skipped.
    """
    try:
        target_date = datetime.strptime(date_input, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD (e.g., 2025-09-29).")
    
    stock_file = os.path.join("Stock Files", f"{target_date.strftime('%Y-%m-%d')}.csv")
    portfolio_file = os.path.join("Portfolio Files", f"{target_date.strftime('%Y-%m-%d')}.csv")
    
    # Check Stock Files exists
    if not os.path.exists(stock_file):
        raise FileNotFoundError(f"No stock data found for {target_date.strftime('%Y-%m-%d')}. Run your stock fetch script first.")
    
    # Check Portfolio exists
    if not os.path.exists(portfolio_file):
        raise FileNotFoundError(f"No portfolio file found for {target_date.strftime('%Y-%m-%d')}. Please create it first.")
    
    # Load stock market data
    stock_df = pd.read_csv(stock_file)
    if 'Symbol' not in stock_df.columns or 'Close' not in stock_df.columns:
        raise ValueError("Stock file is missing required columns: Symbol, Close")
    
    # Load portfolio
    df = pd.read_csv(portfolio_file)
    required_cols = ['Holding Name', 'Buying Price', 'Current Price', 'Number of Units', 'Total Amount', 'Perct Change']
    if not all(col in df.columns for col in required_cols):
        raise ValueError("Portfolio file missing required columns. Expected: Holding Name, Buying Price, Current Price, Number of Units, Total Amount, Perct Change")
    
    # Update portfolio
    for index, row in df.iterrows():
        symbol = row['Holding Name']
        if symbol.lower() == 'cash':   # Skip cash
            continue
        
        match = stock_df[stock_df['Symbol'].str.upper() == symbol.upper()]
        if not match.empty:
            close_price = float(match['Close'].iloc[0])
            df.at[index, 'Current Price'] = round(close_price, 2)
            df.at[index, 'Total Amount'] = round(df.at[index, 'Current Price'] * df.at[index, 'Number of Units'], 2)
            df.at[index, 'Perct Change'] = round(
                ((df.at[index, 'Current Price'] - df.at[index, 'Buying Price']) / df.at[index, 'Buying Price']) * 100, 2
            )
        else:
            print(f"No stock data found for {symbol} in Stock Files on {date_input} — skipping update.")
    
    # Save updated portfolio
    df.to_csv(portfolio_file, index=False)
    print(f"Updated portfolio file using Stock Files data for {target_date.strftime('%Y-%m-%d')}: {portfolio_file}")

if __name__ == "__main__":
    date_input = input("Enter the date (YYYY-MM-DD): ").strip()
    try:
        update_portfolio(date_input)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
