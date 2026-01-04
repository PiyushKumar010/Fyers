""
Test script for TrendAnalyzer class
"""
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import pytz

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after setting up path
from indicators.trend_analyzer import TrendAnalyzer

# Mock Fyers client for testing
class MockFyersClient:
    def __init__(self, mock_data=None):
        self.mock_data = mock_data or []
        
    def history(self, data):
        # Return mock data in the same format as Fyers API
        return {'candles': self.mock_data}

def test_trend_analyzer():
    """Test the TrendAnalyzer with mock data"""
    print("\n=== Testing TrendAnalyzer ===")
    
    # Create mock data for testing
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    timestamps = [(now - timedelta(minutes=i*5)).timestamp() for i in range(20)]
    
    # Create a simple uptrend pattern
    mock_data = []
    for i, ts in enumerate(sorted(timestamps)):
        # Create an uptrend pattern
        if i < 10:  # First 10 candles: downtrend
            open_price = 100 - i
            close_price = 99 - i
            high = open_price + 0.5
            low = close_price - 0.5
        else:  # Last 10 candles: uptrend
            open_price = 90 + (i-10)
            close_price = 91 + (i-10)
            high = close_price + 0.5
            low = open_price - 0.5
            
        mock_data.append([int(ts), open_price, high, low, close_price, 1000])
    
    # Initialize mock client and analyzer
    mock_client = MockFyersClient(mock_data)
    analyzer = TrendAnalyzer(mock_client)
    
    # Test trend detection
    df = pd.DataFrame(mock_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
    df['Timestamp'] = df['Timestamp'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
    
    trend = analyzer.detect_trend(df)
    print(f"\nDetected Trend: {trend}")
    
    # Test Stochastic calculation
    df_with_stoch = analyzer.calculate_stochastic_oscillator(df)
    print("\nStochastic Oscillator values:")
    print(df_with_stoch[['Close', 'K', 'D']].tail())
    
    # Test full analysis
    print("\nFull Market Analysis:")
    analysis = analyzer.analyze_market("NSE:RELIANCE-EQ", "5", 1)
    for key, value in analysis.items():
        print(f"{key}: {value}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_trend_analyzer()
