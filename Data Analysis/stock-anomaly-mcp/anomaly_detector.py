"""
Simple anomaly detection using hardcoded logic
Triggers alerts ~40% of the time
"""
import random

class StockAnomalyDetector:
    def __init__(self, window_size=20, contamination=0.15):
        """
        window_size: number of recent prices to consider
        contamination: not used in simple version, kept for compatibility
        """
        self.window_size = window_size
        self.price_history = {}
        self.alert_counter = 0
        print(f"✓ Anomaly Detector initialized (window_size={window_size})")
        
    def update_and_detect(self, symbol, price):
        """
        Simple hardcoded anomaly detection logic
        Returns: (is_anomaly, anomaly_score, price_change_pct)
        """
        # Initialize history for new symbol
        if symbol not in self.price_history:
            self.price_history[symbol] = []
            print(f"📊 New symbol tracked: {symbol}")
            
        # Add current price
        self.price_history[symbol].append(price)
        
        # Keep only recent window
        if len(self.price_history[symbol]) > self.window_size:
            self.price_history[symbol] = self.price_history[symbol][-self.window_size:]
        
        # Need minimum data points
        if len(self.price_history[symbol]) < 2:
            return False, 0.0, 0.0
        
        # Calculate price change percentage
        previous_price = self.price_history[symbol][-2]
        pct_change = ((price - previous_price) / previous_price) * 100
        
        # Simple hardcoded logic to trigger alerts ~40% of the time
        is_anomaly = False
        anomaly_score = 0.0
        
        # Rule 1: Large price changes (>2% or <-2%) - always flag
        if abs(pct_change) > 2.0:
            is_anomaly = True
            anomaly_score = abs(pct_change) / 10.0
            print(f"🔴 Rule 1 triggered: Large change detected for {symbol}: {pct_change:.2f}%")
        
        # Rule 2: Moderate changes (>1% or <-1%) - flag 50% of the time
        elif abs(pct_change) > 1.0:
            if random.random() < 0.5:
                is_anomaly = True
                anomaly_score = abs(pct_change) / 15.0
                print(f"🟡 Rule 2 triggered: Moderate change for {symbol}: {pct_change:.2f}%")
        
        # Rule 3: Small changes - flag 30% of the time to reach ~40% total
        else:
            if random.random() < 0.3:
                is_anomaly = True
                anomaly_score = abs(pct_change) / 20.0
                print(f"🟢 Rule 3 triggered: Small change flagged for {symbol}: {pct_change:.2f}%")
        
        # Track alert statistics
        if is_anomaly:
            self.alert_counter += 1
        
        return is_anomaly, float(anomaly_score), float(pct_change)