import pandas as pd
import os
from datetime import datetime

def get_portfolio_string(date_input: str, default_cash: float = 25000.00) -> str:
    """
    Reads the portfolio CSV for the given date and returns a formatted portfolio string.
    If the CSV is empty (only headers), assumes portfolio is entirely in cash with default_cash value.
    
    Args:
        date_input (str): Date in YYYY-MM-DD format.
        default_cash (float): Default cash amount for empty portfolio (default: 100.00).
    
    Returns:
        str: Formatted portfolio string.
    
    Raises:
        ValueError: If date format is invalid or CSV is missing required columns.
        FileNotFoundError: If CSV file does not exist.
    """
    output_dir = "Portfolio Files"
    
    try:
        target_date = datetime.strptime(date_input, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD (e.g., 2025-09-17).")
    
    csv_file = os.path.join(output_dir, f"{target_date.strftime('%Y-%m-%d')}.csv")
    
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"No portfolio file found for {target_date.strftime('%Y-%m-%d')}. Please create it first.")
    
    # Read CSV with error handling
    df = pd.read_csv(csv_file)
    required_cols = ['Holding Name', 'Buying Price', 'Current Price', 'Number of Units', 'Total Amount', 'Perct Change']
    
    # Check for required columns
    if not all(col in df.columns for col in required_cols):
        raise ValueError("CSV missing required columns. Expected: Holding Name, Buying Price, Current Price, Number of Units, Total Amount, Perct Change")
    
    # Handle empty CSV (only headers)
    if df.empty:
        portfolio_str = f"Total Portfolio Value: ₹{default_cash:.2f} (Invested: ₹{default_cash:.2f}, Change: +0.00%)\n\n"
        portfolio_str += "Holdings:\n"
        portfolio_str += f"- Cash: 1 unit @ Buy ₹{default_cash:.2f}, Current ₹{default_cash:.2f}, Value ₹{default_cash:.2f}, Change +0.00%\n"
        return portfolio_str
    
    # Process non-empty CSV
    total_invested = (df['Buying Price'] * df['Number of Units']).sum()
    total_portfolio_value = df['Total Amount'].sum()
    total_pct_change = ((total_portfolio_value - total_invested) / total_invested * 100) if total_invested > 0 else 0
    
    portfolio_str = f"Total Portfolio Value: ₹{total_portfolio_value:.2f} (Invested: ₹{total_invested:.2f}, Change: {total_pct_change:+.2f}%)\n\n"
    portfolio_str += "Holdings:\n"
    for _, row in df.iterrows():
        pct_change = row['Perct Change']
        portfolio_str += f"- {row['Holding Name']}: {int(row['Number of Units'])} units @ Buy ₹{row['Buying Price']:.2f}, Current ₹{row['Current Price']:.2f}, Value ₹{row['Total Amount']:.2f}, Change {pct_change:+.2f}%\n"
    
    return portfolio_str