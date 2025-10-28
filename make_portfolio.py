import json
import pandas as pd
import re
import os


def extract_inner_json(data):
    """Extracts and returns the parsed inner JSON from either OpenAI or Gemini response."""
    # --- Handle OpenAI JSON structure ---
    if "choices" in data and data["choices"][0]["message"].get("content"):
        content = data["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON inside code fences
            match = re.search(r"```json(.*?)```", content, re.DOTALL)
            if match:
                return json.loads(match.group(1).strip())
            raise

    # --- Handle Gemini JSON structure ---
    elif "text" in data:
        text = data["text"]
        match = re.search(r"```json(.*?)```", text, re.DOTALL)
        if match:
            inner = match.group(1).strip()
            return json.loads(inner)
        else:
            return json.loads(text)

    else:
        raise ValueError("Unrecognized JSON structure (neither OpenAI nor Gemini).")


def update_portfolio(input_date, output_date):
    """Updates the portfolio CSV for the given output date using either OpenAI or Gemini JSON format."""
    json_path = f"Grok Daily Reviews/Weekends/t_{input_date}.json"
    csv_input_path = f"Portfolio Files/{input_date}.csv"
    csv_output_path = f"Portfolio Files/{output_date}.csv"

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    if not os.path.exists(csv_input_path):
        raise FileNotFoundError(f"CSV file not found: {csv_input_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        outer_data = json.load(f)

    # Parse content from Gemini or OpenAI response
    inner_data = extract_inner_json(outer_data)

    # --- Normalize trades list ---
    # Gemini uses "emergency_trades" for sells and "top_signals" for buys
    trades = []

    if "trades" in inner_data:
        # OpenAI format
        trades = inner_data["trades"]

    elif "emergency_trades" in inner_data or "top_signals" in inner_data:
        if "emergency_trades" in inner_data:
            for t in inner_data["emergency_trades"]:
                trades.append({
                    "symbol": t["symbol"],
                    "action": t["action"].lower(),  # e.g., 'sell'
                    "shares": t.get("quantity", 0),
                    "amount": round(t["price"] * t.get("quantity", 0), 2)
                })
        if "top_signals" in inner_data:
            for t in inner_data["top_signals"]:
                trades.append({
                    "symbol": t["symbol"],
                    "action": "buy",
                    "shares": 1,  # Assume 1 share for new additions unless specified
                    "amount": round(t["price"], 2)
                })
    else:
        raise ValueError("No trades, top_signals, or emergency_trades found in JSON.")

    # --- Load portfolio CSV ---
    df = pd.read_csv(csv_input_path)

    # Extract and remove cash
    cash_row = df[df["Holding Name"] == "Cash"]
    if cash_row.empty:
        cash = 0.0
    else:
        cash = cash_row["Total Amount"].values[0]
        df = df[df["Holding Name"] != "Cash"]

    # --- Process trades ---
    for trade in trades:
        action = trade["action"].lower()
        symbol = trade["symbol"]
        shares = trade["shares"]
        amount = round(trade["amount"], 2)
        price = round(amount / shares, 2) if shares > 0 else 0.0

        if action == "remove":
            continue

        if action == "sell":
            cash += amount
            idx = df[df["Holding Name"] == symbol].index
            if not idx.empty:
                current_units = df.at[idx[0], "Number of Units"]
                new_units = current_units - shares
                if new_units > 0:
                    df.at[idx[0], "Number of Units"] = new_units
                    df.at[idx[0], "Current Price"] = price
                    df.at[idx[0], "Total Amount"] = round(price * new_units, 2)
                    buying_price = df.at[idx[0], "Buying Price"]
                    df.at[idx[0], "Perct Change"] = round(
                        ((price - buying_price) / buying_price) * 100, 2)
                else:
                    df = df.drop(idx[0])

        elif action == "buy":
            cash -= amount
            idx = df[df["Holding Name"] == symbol].index
            if not idx.empty:
                old_units = df.at[idx[0], "Number of Units"]
                old_buy = df.at[idx[0], "Buying Price"]
                old_cost = round(old_buy * old_units, 2)
                new_cost = amount
                new_units = old_units + shares
                new_buy = round((old_cost + new_cost) / new_units, 2)
                df.at[idx[0], "Buying Price"] = new_buy
                df.at[idx[0], "Current Price"] = price
                df.at[idx[0], "Number of Units"] = new_units
                df.at[idx[0], "Total Amount"] = round(price * new_units, 2)
                df.at[idx[0], "Perct Change"] = round(
                    ((price - new_buy) / new_buy) * 100, 2)
            else:
                new_row = {
                    "Holding Name": symbol,
                    "Buying Price": price,
                    "Current Price": price,
                    "Number of Units": shares,
                    "Total Amount": amount,
                    "Perct Change": 0.00,
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # --- Add cash row back ---
    cash = round(cash, 2)
    cash_row = pd.DataFrame({
        "Holding Name": ["Cash"],
        "Buying Price": [cash],
        "Current Price": [cash],
        "Number of Units": [1],
        "Total Amount": [cash],
        "Perct Change": [0.00],
    })
    df = pd.concat([df, cash_row], ignore_index=True)

    # --- Round numeric values ---
    for col in ["Buying Price", "Current Price", "Total Amount", "Perct Change"]:
        df[col] = df[col].round(2)

    df.to_csv(csv_output_path, index=False)
    print(f"✅ Portfolio successfully updated for {output_date}: {csv_output_path}")


if __name__ == "__main__":
    input_date = input("Enter date for JSON and CSV input (YYYY-MM-DD): ").strip()
    output_date = input("Enter date for CSV output (YYYY-MM-DD): ").strip()
    update_portfolio(input_date, output_date)
