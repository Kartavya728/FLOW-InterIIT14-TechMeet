"""
Simulates real-time stock price streaming using Yahoo Finance data
"""
import yfinance as yf
import time
from datetime import datetime
import os

def fetch_and_stream_stock_data(symbols=['AAPL', 'GOOGL', 'MSFT', 'TSLA'], interval='1m'):
    """
    Fetch real stock data and simulate streaming
    """
    print(f"Fetching data for {symbols}...")
    print("Starting stream... (Press Ctrl+C to stop)")
    os.makedirs('data', exist_ok=True)
    if not os.path.exists('data/stock_stream.csv'):
        with open('data/stock_stream.csv', 'w') as f:
            f.write("symbol,price,volume,timestamp\n")
    while True:
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                df = stock.history(period='1d', interval='1m')
                if not df.empty:
                    latest = df.iloc[-1]
                    timestamp = datetime.now().isoformat()
                    with open('data/stock_stream.csv', 'a') as f:
                        line = f"{symbol},{latest['Close']:.2f},{int(latest['Volume'])},{timestamp}\n"
                        f.write(line)
                    print(f"✓ {symbol}: ${latest['Close']:.2f} | Vol: {int(latest['Volume']):,} | {timestamp[:19]}")
                else:
                    print(f"⚠ No data for {symbol}")
            except Exception as e:
                print(f"✗ Error fetching {symbol}: {e}")
        print(f"\n{'='*70}")
        print(f"Sleeping 20 seconds... (next update at {datetime.now().strftime('%H:%M:%S')})")
        print(f"{'='*70}\n")
        time.sleep(3)

if __name__ == "__main__":
    print("\n" + "="*70)
    print("Stock Price Streamer - Yahoo Finance")
    print("="*70 + "\n")
    try:
        fetch_and_stream_stock_data()
    except KeyboardInterrupt:
        print("\n\n✓ Streamer stopped by user.")