import pandas as pd
import datetime
from datetime import timedelta
from tqdm import tqdm
import time
import os
import warnings
from nsepython import *
from dateutil.parser import parse

warnings.filterwarnings('ignore')


def fetch_ohlcv(symbols, target_date):
    """Fetch OHLCV data for symbols on the target date using nsepython only."""
    start = target_date.strftime('%d-%m-%Y')
    end = start  # same day
    data_list = []

    for symbol in tqdm(symbols, desc="Fetching OHLCV"):
        try:
            symbol_clean = symbol.replace('.NS', '')

            df = equity_history(symbol_clean, "EQ", start, end)

            if df.empty:
                print(f"No data for {symbol_clean} on {target_date.strftime('%Y-%m-%d')}")
                continue

            row = df.iloc[0]
            data_list.append({
                'Symbol': symbol_clean,
                'Date': target_date.strftime('%Y-%m-%d'),
                'Open': float(row['CH_OPENING_PRICE']),
                'High': float(row['CH_TRADE_HIGH_PRICE']),
                'Low': float(row['CH_TRADE_LOW_PRICE']),
                'Close': float(row['CH_CLOSING_PRICE']),
                'Volume': int(row['CH_TOT_TRADED_QTY'])
            })

            time.sleep(0.5)  # avoid hitting API limits
        except Exception as e:
            print(f"nsepython failed for {symbol}: {e}")
            continue

    return pd.DataFrame(data_list)


def fetch_stock_data(date_input: str) -> pd.DataFrame:
    """
    Fetches end-of-day OHLCV data for top 75 mid-cap and small-cap NSE stocks on the given date,
    sorts by volume, saves to CSV in "Stock Files" folder, and returns the combined DataFrame.
    """
    output_dir = "Stock Files"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        target_date = datetime.datetime.strptime(date_input, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD (e.g., 2025-09-17).")

    print(f"\nFetching data for {target_date.strftime('%Y-%m-%d')}...")

    mid_symbols = [
        'ADANIENT.NS', 'APOLLOHOSP.NS', 'VBL.NS', 'PAGEIND.NS', 'PERSISTENT.NS', 'ABB.NS', 'AUBANK.NS', 'GODREJCP.NS',
        'POLICYBZR.NS', 'INDUSINDBK.NS', 'CUMMINSIND.NS', 'DIXON.NS', 'HAVELLS.NS', 'AMBUJACEM.NS', 'PIDILITIND.NS', 'TORNTPOWER.NS',
        'LUPIN.NS', 'BHEL.NS', 'ABBOTINDIA.NS', 'TATACHEM.NS', 'ESCORTS.NS', 'MUTHOOTFIN.NS', 'DABUR.NS', 'CORF.NS',
        'CHOLAFIN.NS', 'COLPAL.NS', 'MPHASIS.NS', 'TATAELXSI.NS', 'BIOCON.NS', 'SUNDARMFIN.NS', 'KPIL.NS', 'LAURUSLABS.NS',
        'TRENT.NS', 'LICI.NS', 'BIRLACORPN.NS', 'TATACOMM.NS', 'GAIL.NS', 'JINDALSTEL.NS', 'NAUKRI.NS', 'LTF.NS', 'KPITTECH.NS',
        'OFSS.NS', 'JUBLFOOD.NS', 'SYNGENE.NS', 'ZYDUSLIFE.NS', 'ALKEM.NS', 'HDFCAMC.NS', 'MAZDOCK.NS', 'MAXHEALTH.NS', 'POLYCAB.NS',
        'MANKIND.NS', 'WAAREEENER.NS', 'UNIONBANK.NS', 'GMRAIRPORT.NS', 'INDUSTOWER.NS', 'MARICO.NS', 'INDIANB.NS', 'BSE.NS',
        'NHPC.NS', 'NTPCGREEN.NS', 'SRF.NS', 'BHARTIHEXA.NS', 'SBICARD.NS', 'ASHOKLEY.NS', 'PAYTM.NS', 'UNOMINDA.NS',
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