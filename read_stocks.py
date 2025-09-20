import pandas as pd
import os
from datetime import datetime

def get_stock_data_string(date_input: str) -> str:
    """
    Reads the stock CSV for the given date and returns a formatted OHLCV string.
    
    Args:
        date_input (str): Date in YYYY-MM-DD format.
    
    Returns:
        str: Formatted stock data string.
    
    Raises:
        ValueError: If date format is invalid.
        FileNotFoundError: If CSV file does not exist.
        ValueError: If CSV is missing required columns.
    """
    output_dir = "Stock Files"
    
    try:
        target_date = datetime.strptime(date_input, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD (e.g., 2025-09-17).")
    
    csv_file = os.path.join(output_dir, f"{target_date.strftime('%Y-%m-%d')}.csv")
    
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"No stock file found for {target_date.strftime('%Y-%m-%d')}. Please create it first.")
    
    df = pd.read_csv(csv_file)
    required_cols = ['Symbol', 'Category', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in df.columns for col in required_cols):
        raise ValueError("CSV missing required columns. Expected: Symbol, Category, Date, Open, High, Low, Close, Volume")
    
    if df.empty:
        return f"No stock data available for {target_date.strftime('%Y-%m-%d')}."
    
    stock_str = f"Stock Data for {target_date.strftime('%Y-%m-%d')} ({len(df)} stocks total):\n\n"
    
    for category in sorted(df['Category'].unique()):
        cat_df = df[df['Category'] == category].sort_values('Volume', ascending=False)
        stock_str += f"{category} Stocks:\n"
        for _, row in cat_df.iterrows():
            stock_str += f"- {row['Symbol']}: O ₹{row['Open']:.2f}, H ₹{row['High']:.2f}, L ₹{row['Low']:.2f}, C ₹{row['Close']:.2f}, Vol {row['Volume']:,.0f}\n"
        stock_str += "\n"
    
    return stock_str