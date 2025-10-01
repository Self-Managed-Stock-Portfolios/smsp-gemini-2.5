import pandas as pd
import os
from datetime import datetime
from nsepython import equity_history

def update_portfolio(date_input: str) -> None:
    """Updates portfolio CSV for the given date using NSE OHLCV data of that date only.
    
    - Current Price, Total Amount, and Perct Change are updated
      strictly with the Close price of the input date.
    - If no data is available (holiday/non-trading day), row is skipped.
    """
    try:
        target_date = datetime.strptime(date_input, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD (e.g., 2025-09-29).")
    
    output_dir = "Portfolio Files"
    csv_file = os.path.join(output_dir, f"{target_date.strftime('%Y-%m-%d')}.csv")
    
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"No portfolio file found for {target_date.strftime('%Y-%m-%d')}. Please create it first.")
    
    df = pd.read_csv(csv_file)
    required_cols = ['Holding Name', 'Buying Price', 'Current Price', 'Number of Units', 'Total Amount', 'Perct Change']
    if not all(col in df.columns for col in required_cols):
        raise ValueError("CSV missing required columns. Expected: Holding Name, Buying Price, Current Price, Number of Units, Total Amount, Perct Change")
    
    # NSE date format: dd-mm-yyyy
    nse_date = target_date.strftime('%d-%m-%Y')
    
    for index, row in df.iterrows():
        symbol = row['Holding Name']
        if symbol.lower() == 'cash':   # Skip cash
            continue
        
        try:
            # Fetch OHLCV for exactly that date
            hist = equity_history(symbol, "EQ", nse_date, nse_date)
            
            if not hist.empty:
                close_price = float(hist['CH_CLOSING_PRICE'].iloc[0])
                df.at[index, 'Current Price'] = round(close_price, 2)
                df.at[index, 'Total Amount'] = round(df.at[index, 'Current Price'] * df.at[index, 'Number of Units'], 2)
                df.at[index, 'Perct Change'] = round(
                    ((df.at[index, 'Current Price'] - df.at[index, 'Buying Price']) / df.at[index, 'Buying Price']) * 100, 2
                )
            else:
                print(f"No trading data for {symbol} on {nse_date} (non-trading day?) — skipping update.")
        
        except Exception as e:
            print(f"Error fetching NSE data for {symbol} on {nse_date}: {e}")
    
    df.to_csv(csv_file, index=False)
    print(f"Updated portfolio file strictly for {target_date.strftime('%Y-%m-%d')}: {csv_file}")

if __name__ == "__main__":
    date_input = input("Enter the date (YYYY-MM-DD): ").strip()
    try:
        update_portfolio(date_input)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")