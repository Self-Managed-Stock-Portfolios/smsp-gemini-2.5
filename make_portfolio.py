
import pandas as pd
import yfinance as yf
import os
import json
from datetime import datetime, timedelta

def auto_update_portfolio(json_date: str, csv_date: str, api_type: str = "gemini") -> None:
    """Updates portfolio CSV for csv_date using JSON response from json_date.
    
    Args:
        json_date (str): Date for JSON file in YYYY-MM-DD format (e.g., '2025-09-26').
        csv_date (str): Date for output CSV in YYYY-MM-DD format (e.g., '2025-09-29').
        api_type (str): API response type ('gemini' or 'grok') to parse JSON.
    
    Raises:
        ValueError: If date format is invalid.
        FileNotFoundError: If JSON file or output directory is missing.
        json.JSONDecodeError: If JSON parsing fails.
    """
    try:
        json_target = datetime.strptime(json_date, '%Y-%m-%d')
        datetime.strptime(csv_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD (e.g., 2025-09-26).")
    
    base_dir = "Gemini Daily Reviews" if api_type == "gemini" else "Grok Daily Reviews"
    sub_dir = "Weekends" if json_target.weekday() < 5 else "Weekends"
    json_file = os.path.join(base_dir, sub_dir, f"t_{json_target.strftime('%Y-%m-%d')}.json")
    if not os.path.exists(json_file):
        raise FileNotFoundError(f"JSON file not found: {json_file}")
    
    output_dir = "Portfolio Files"
    os.makedirs(output_dir, exist_ok=True)
    csv_file = os.path.join(output_dir, f"{csv_date}.csv")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    try:
        signal_content = json.loads(json_data['text'].strip('```json').rstrip('```').strip()) if api_type == "gemini" else json.loads(json_data['choices'][0]['message']['content'])
    except KeyError:
        raise json.JSONDecodeError("Invalid JSON format: missing 'text' or 'choices'", "", 0)
    
    trades = {trade['symbol']: trade for trade in signal_content['trades'] if trade['action'] != 'remove'}
    portfolio = signal_content['portfolio']
    
    data = []
    for holding in portfolio['holdings']:
        symbol = holding.split(':')[0].strip()
        if symbol in trades:
            trade = trades[symbol]
            shares = trade['shares']
            buy_price = round(trade['amount'] / shares, 2) if shares > 0 else 0.0
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                hist = ticker.history(start=json_target, end=json_target + timedelta(days=1))
                if not hist.empty:
                    current_price = round(hist['Close'].iloc[0], 2)
                    total_amount = round(current_price * shares, 2)
                    perct_change = round(((current_price - buy_price) / buy_price) * 100, 2) if buy_price > 0 else 0.0
                else:
                    print(f"No data for {symbol} on {json_date}")
                    current_price = buy_price
                    total_amount = round(buy_price * shares, 2)
                    perct_change = 0.0
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                current_price = buy_price
                total_amount = round(buy_price * shares, 2)
                perct_change = 0.0
            data.append({
                'Holding Name': symbol,
                'Buying Price': buy_price,
                'Current Price': current_price,
                'Number of Units': shares,
                'Total Amount': total_amount,
                'Perct Change': perct_change
            })
    
    if portfolio['cash'] > 0:
        data.append({
            'Holding Name': 'Cash',
            'Buying Price': 1.00,
            'Current Price': 1.00,
            'Number of Units': portfolio['cash'],
            'Total Amount': portfolio['cash'],
            'Perct Change': 0.00
        })
    
    df = pd.DataFrame(data)
    df.to_csv(csv_file, index=False)
    print(f"Updated portfolio file: {csv_file}")

if __name__ == "__main__":
    json_date = input("Enter the JSON date (YYYY-MM-DD): ").strip()
    csv_date = input("Enter the CSV output date (YYYY-MM-DD): ").strip()
    api_type = input("Enter API type (gemini or grok): ").strip().lower()
    if api_type not in ['gemini', 'grok']:
        print("Invalid API type. Please enter 'gemini' or 'grok'.")
        exit(1)
    try:
        auto_update_portfolio(json_date, csv_date, api_type)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: {e}")
