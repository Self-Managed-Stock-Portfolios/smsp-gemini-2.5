import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm
import time
import os
import warnings
warnings.filterwarnings('ignore')

def fetch_ohlcv(symbols, target_date):
    """Fetch OHLCV data for symbols on the target date using yfinance."""
    start_date = target_date
    end_date = target_date + timedelta(days=1)
    data_list = []
    for symbol in tqdm(symbols, desc="Fetching OHLCV"):
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            if not hist.empty and len(hist) > 0:
                row = hist.iloc[0]
                data_list.append({
                    'Symbol': symbol.replace('.NS', ''), 
                    'Date': row.name.strftime('%Y-%m-%d'),
                    'Open': round(row['Open'], 2),
                    'High': round(row['High'], 2),
                    'Low': round(row['Low'], 2),
                    'Close': round(row['Close'], 2),
                    'Volume': int(row['Volume'])
                })
            time.sleep(0.5)
        except Exception as e:
            continue
    return pd.DataFrame(data_list)

def fetch_stock_data(date_input: str) -> pd.DataFrame:
    """
    Fetches end-of-day OHLCV data for top 75 mid-cap and small-cap NSE stocks on the given date,
    sorts by volume, saves to CSV in "Stock Files" folder, and returns the combined DataFrame.
    
    Args:
        date_input (str): Date in YYYY-MM-DD format.
    
    Returns:
        pd.DataFrame: Combined DataFrame with fetched and processed stock data.
    
    Raises:
        ValueError: If date format is invalid.
    """
    output_dir = "Stock Files"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        target_date = datetime.strptime(date_input, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD (e.g., 2025-09-17).")
    
    print(f"\nFetching data for {target_date.strftime('%Y-%m-%d')}...")

    mid_symbols = [
        'ADANIENT.NS', 'APOLLOHOSP.NS', 'VBL.NS', 'PAGEIND.NS', 'PERSISTENT.NS', 'ABB.NS', 'SUZLON.NS', 'AUBANK.NS', 'GODREJCP.NS',
        'POLICYBZR.NS', 'INDUSINDBK.NS', 'CUMMINSIND.NS', 'DIXON.NS', 'HAVELLS.NS', 'AMBUJACEM.NS', 'PIDILITIND.NS', 'TORNTPOWER.NS',
        'LUPIN.NS', 'BHEL.NS', 'ABBOTINDIA.NS', 'TATACHEM.NS', 'ESCORTS.NS', 'MUTHOOTFIN.NS', 'DABUR.NS', 'CORF.NS',
        'CHOLAFIN.NS', 'COLPAL.NS', 'MPHASIS.NS', 'TATAELXSI.NS', 'BIOCON.NS', 'SUNDARMFIN.NS', 'KPIL.NS', 'LAURUSLABS.NS',
        'TRENT.NS', 'LICI.NS', 'BIRLACORPN.NS', 'TATACOMM.NS', 'GAIL.NS', 'JINDALSTEL.NS', 'NAUKRI.NS', 'LTF.NS', 'KPITTECH.NS',
        'OFSS.NS', 'JUBLFOOD.NS', 'SYNGENE.NS', 'ZYDUSLIFE.NS', 'ALKEM.NS', 'HDFCAMC.NS', 'MAZDOCK.NS', 'MAXHEALTH.NS', 'POLYCAB.NS',
        'MANKIND.NS', 'WAAREEENER.NS', 'UNIONBANK.NS', 'GMRAIRPORT.NS', 'INDUSTOWER.NS', 'MARICO.NS', 'INDIANB.NS', 'BSE.NS',
        'NHPC.NS', 'NTPCGREEN.NS', 'SRF.NS', 'BHARTIHEXA.NS', 'IDEA.NS', 'SBICARD.NS', 'ASHOKLEY.NS', 'PAYTM.NS', 'UNOMINDA.NS',
        'ABCAPITAL.NS', 'RVNL.NS', 'FORTIS.NS', 'VOLTAS.NS', 'PRESTIGE.NS', 'NYKAA.NS', 'LLOYDSME.NS'
    ]

    small_symbols = [
        'IDBI.NS', 'IOB.NS', 'FACT.NS', 'GODFRYPHLP.NS', 'AIIL.NS', 'KAYNES.NS', 'LAURUSLABS.NS', 'MCX.NS', 'RADICO.NS', 'UCOBANK.NS',
        'SUVEN.NS', 'CHOLAHLDNG.NS', 'NH.NS', 'POONAWALLA.NS', 'DELHIVERY.NS', 'CENTRALBK.NS', 'CDSL.NS', 'GODIGIT.NS', 'GILLETTE.NS',
        'ASTERDM.NS', 'ITI.NS', 'AFFLE.NS', 'GRSE.NS', 'KIMS.NS', 'NBCC.NS', 'SUMICHEM.NS', 'AEGISLOG.NS', 'AMBER.NS', 'HINDCOPPER.NS',
        'LALPATHLAB.NS', 'PPLPHARMA.NS', 'JBCHEPHARM.NS', 'PEL.NS', 'FSL.NS', 'INOXWIND.NS', 'ZFCVINDIA.NS', 'EMCURE.NS', 'TATACHEM.NS',
        'SHYAMMETL.NS', 'NAVINFLUOR.NS', 'ANANDRATHI.NS', 'EIHOTEL.NS', 'WOCKPHARMA.NS', 'RAMCOCEM.NS', 'MANAPPURAM.NS', 'IDEA.NS',
        'VSTIND.NS', 'RAJESHEXPO.NS', 'GMRINFRA.NS', 'IRCON.NS', 'BEML.NS', 'IRCTC.NS', 'HUDCO.NS', 'HAL.NS', 'SAIL.NS', 'BEL.NS',
        'COFORGE.NS', 'KPIGREEN.NS', 'CROMPTON.NS', 'THERMAX.NS', 'ASTRAL.NS', 'METROPOLIS.NS', 'SJVN.NS', 'IRB.NS', 'RBLBANK.NS',
        'INDIAMART.NS', 'DEEPAKNTR.NS', 'LMW.NS', 'CREDITACC.NS', 'NAVA.NS', 'KEI.NS', 'OBEROIRLTY.NS', 'RATNAMANI.NS'
    ]

    all_categories = [
        ('Mid Cap', mid_symbols),
        ('Small Cap', small_symbols)
    ]

    combined_df = pd.DataFrame()

    for category, symbols in all_categories:
        print(f"\nProcessing {category} ({len(symbols)} symbols)...")
        df = fetch_ohlcv(symbols, target_date)
        if df.empty:
            print(f"No data available for {category} on {target_date.strftime('%Y-%m-%d')}.")
            continue
        df = df.sort_values('Volume', ascending=False).head(75)
        df['Category'] = category
        combined_df = pd.concat([combined_df, df], ignore_index=True)

        print(f"Fetched {len(df)} stocks for {category}")

    combined_df = combined_df.drop_duplicates(subset=['Symbol', 'Date'])

    output_file = os.path.join(output_dir, f"{target_date.strftime('%Y-%m-%d')}.csv")
    if not combined_df.empty:
        combined_df.to_csv(output_file, index=False)
        print(f"\nSaved {len(combined_df)} rows to {output_file}")
        print("\nSample data:")
        print(combined_df.head())
    else:
        empty_df = pd.DataFrame(columns=['Symbol', 'Category', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        empty_df.to_csv(output_file, index=False)
        print(f"No data for {target_date.strftime('%Y-%m-%d')} (non-trading day?). Created empty {output_file}.")
    
    return combined_df

if __name__ == "__main__":
    date_input = input("Enter the date (YYYY-MM-DD): ").strip()
    df = fetch_stock_data(date_input)