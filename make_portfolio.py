import json
import pandas as pd
import re
import os


def extract_inner_json(data):
    """Extracts and returns the parsed inner JSON from a Gemini response."""
    if "text" not in data:
        raise ValueError("Invalid Gemini response: missing 'text' field.")

    text = data["text"].strip()

    # Extract JSON between ```json ... ``` if present
    match = re.search(r"```json(.*?)```", text, re.DOTALL)
    if match:
        inner = match.group(1).strip()
        return json.loads(inner)

    # Fallback: try direct JSON parsing
    if text.startswith("json\n"):
        text = text[5:].strip()
    return json.loads(text)


def update_portfolio(input_date, output_date):
    """Updates the portfolio CSV for the given output date using Gemini JSON format."""
    json_path = f"Gemini Daily Reviews/Weekends/t_{input_date}.json"
    csv_input_path = f"Portfolio Files/{input_date}.csv"
    csv_output_path = f"Portfolio Files/{output_date}.csv"

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    if not os.path.exists(csv_input_path):
        raise FileNotFoundError(f"CSV file not found: {csv_input_path}")

    # --- Load Gemini JSON ---
    with open(json_path, "r", encoding="utf-8") as f:
        outer_data = json.load(f)

    # Extract actual trading instructions
    inner_data = extract_inner_json(outer_data)

    if "trades" not in inner_data:
        raise ValueError("Gemini JSON missing 'trades' section.")

    trades = inner_data["trades"]

    # --- Load portfolio CSV ---
    df = pd.read_csv(csv_input_path)

    # Extract and remove cash row
    cash_row = df[df["Holding Name"].str.lower() == "cash"]
    cash = float(cash_row["Total Amount"].values[0]) if not cash_row.empty else 0.0
    df = df[df["Holding Name"].str.lower() != "cash"]

    # --- Process trades from Gemini ---
    for trade in trades:
        action = trade["action"].lower()
        symbol = trade["symbol"]
        shares = trade.get("shares", 0)
        amount = round(trade.get("amount", 0.0), 2)
        price = round(amount / shares, 2) if shares > 0 else 0.0

        if action == "remove":
            # Simply drop the stock from the portfolio
            idx = df[df["Holding Name"] == symbol].index
            if not idx.empty:
                df = df.drop(idx[0])
            continue

        if action == "sell":
            # Add to cash, reduce or remove holding
            cash += amount
            idx = df[df["Holding Name"] == symbol].index
            if not idx.empty:
                current_units = df.at[idx[0], "Number of Units"]
                new_units = current_units - shares
                if new_units > 0:
                    df.at[idx[0], "Number of Units"] = new_units
                    df.at[idx[0], "Current Price"] = price
                    df.at[idx[0], "Total Amount"] = round(price * new_units, 2)
                    buy_price = df.at[idx[0], "Buying Price"]
                    df.at[idx[0], "Perct Change"] = round(((price - buy_price) / buy_price) * 100, 2)
                else:
                    df = df.drop(idx[0])

        elif action == "buy":
            # Subtract from cash, add or update holding
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
                df.at[idx[0], "Perct Change"] = round(((price - new_buy) / new_buy) * 100, 2)
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

    # --- Add updated cash row ---
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

    # --- Round and save ---
    for col in ["Buying Price", "Current Price", "Total Amount", "Perct Change"]:
        df[col] = df[col].round(2)

    df.to_csv(csv_output_path, index=False)
    print(f"✅ Portfolio successfully updated for {output_date}: {csv_output_path}")


if __name__ == "__main__":
    input_date = input("Enter input date (YYYY-MM-DD): ").strip()
    output_date = input("Enter output date (YYYY-MM-DD): ").strip()
    update_portfolio(input_date, output_date)
