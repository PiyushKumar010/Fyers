"""
Paper Trading System - Example Usage

Demonstrates how to use the paper trading system with realistic scenarios.
"""

from app.paper_trading import PaperTradingEngine


def example_1_simple_trade():
    """Example 1: Simple Buy-Sell Trade"""
    print("=" * 70)
    print("EXAMPLE 1: Simple Buy-Sell Trade")
    print("=" * 70)
    
    # Initialize engine
    engine = PaperTradingEngine(
        initial_capital=100000,
        brokerage_per_trade=20,
        slippage_percent=0.1,
    )
    
    print(f"\n📊 Initial Portfolio:")
    summary = engine.get_portfolio_summary()
    print(f"   Capital: ₹{summary['current_capital']:,.2f}")
    print(f"   Portfolio Value: ₹{summary['portfolio_value']:,.2f}")
    
    # BUY Order
    print(f"\n📈 Placing BUY order for NSE:RELIANCE-EQ")
    buy_result = engine.place_order(
        symbol='NSE:RELIANCE-EQ',
        side='BUY',
        quantity=10,
        price=2500,
    )
    
    if buy_result['status'] == 'SUCCESS':
        print(f"   ✅ Order Executed")
        print(f"   📝 Order ID: {buy_result['order']['order_id']}")
        print(f"   💰 Executed Price: ₹{buy_result['order']['executed_price']:,.2f}")
        print(f"   💵 Total Cost: ₹{buy_result['trade']['value']:,.2f}")
        print(f"   📊 Brokerage: ₹{buy_result['trade']['brokerage']:,.2f}")
        print(f"   💰 Remaining Capital: ₹{buy_result['portfolio']['current_capital']:,.2f}")
    else:
        print(f"   ❌ Order Rejected: {buy_result['message']}")
        return
    
    # Simulate price movement
    print(f"\n📊 Market Update: Price moved to ₹2,600")
    engine.update_position_prices({'NSE:RELIANCE-EQ': 2600})
    
    # Check unrealized P&L
    positions = engine.get_open_positions()
    if positions:
        pos = positions[0]
        print(f"   📈 Unrealized P&L: ₹{pos['unrealized_pnl']:,.2f} ({pos['unrealized_pnl_percent']:.2f}%)")
    
    # SELL Order
    print(f"\n📉 Placing SELL order for NSE:RELIANCE-EQ")
    sell_result = engine.place_order(
        symbol='NSE:RELIANCE-EQ',
        side='SELL',
        quantity=10,
        price=2600,
    )
    
    if sell_result['status'] == 'SUCCESS':
        print(f"   ✅ Order Executed")
        print(f"   📝 Order ID: {sell_result['order']['order_id']}")
        print(f"   💰 Executed Price: ₹{sell_result['order']['executed_price']:,.2f}")
        print(f"   💵 Total Proceeds: ₹{sell_result['trade']['value']:,.2f}")
        print(f"   💰 Realized P&L: ₹{sell_result['trade']['realized_pnl']:,.2f}")
        print(f"   💰 Final Capital: ₹{sell_result['portfolio']['current_capital']:,.2f}")
    
    # Final Summary
    print(f"\n📊 Final Portfolio:")
    summary = engine.get_portfolio_summary()
    print(f"   Total P&L: ₹{summary['total_pnl']:,.2f}")
    print(f"   Returns: {summary['returns_percent']:.2f}%")
    print(f"   Total Brokerage: ₹{summary['total_brokerage_paid']:,.2f}")


def example_2_stop_loss_target():
    """Example 2: Trade with Stop Loss and Target"""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 2: Trade with Stop Loss and Target")
    print("=" * 70)
    
    engine = PaperTradingEngine(initial_capital=100000)
    
    # BUY with risk management
    print(f"\n📈 Placing BUY order with Stop Loss and Target")
    buy_result = engine.place_order(
        symbol='NSE:TCS-EQ',
        side='BUY',
        quantity=5,
        price=3500,
        stop_loss=3450,  # 1.43% stop loss
        target=3600,     # 2.86% target
    )
    
    if buy_result['status'] == 'SUCCESS':
        print(f"   ✅ Order Executed at ₹{buy_result['order']['executed_price']:,.2f}")
        print(f"   🛡️ Stop Loss: ₹3,450")
        print(f"   🎯 Target: ₹3,600")
    
    # Scenario 1: Target Hit
    print(f"\n📊 Scenario: Price reaches target (₹3,600)")
    engine.update_position_prices({'NSE:TCS-EQ': 3600})
    
    auto_orders = engine.check_stop_loss_targets()
    if auto_orders:
        order = auto_orders[0]
        print(f"   🎯 Target Triggered!")
        print(f"   ✅ Auto-Sold at ₹{order['order']['executed_price']:,.2f}")
        print(f"   💰 Realized P&L: ₹{order['trade']['realized_pnl']:,.2f}")


def example_3_multiple_positions():
    """Example 3: Managing Multiple Positions"""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 3: Managing Multiple Positions")
    print("=" * 70)
    
    engine = PaperTradingEngine(
        initial_capital=100000,
        max_positions=5,
        max_position_size=0.25,  # 25% per position
    )
    
    # Open multiple positions
    stocks = [
        {'symbol': 'NSE:RELIANCE-EQ', 'price': 2500, 'qty': 8},
        {'symbol': 'NSE:TCS-EQ', 'price': 3500, 'qty': 5},
        {'symbol': 'NSE:INFY-EQ', 'price': 1400, 'qty': 15},
    ]
    
    print(f"\n📈 Opening multiple positions:")
    for stock in stocks:
        result = engine.place_order(
            symbol=stock['symbol'],
            side='BUY',
            quantity=stock['qty'],
            price=stock['price'],
        )
        if result['status'] == 'SUCCESS':
            print(f"   ✅ {stock['symbol']}: {stock['qty']} @ ₹{stock['price']}")
        else:
            print(f"   ❌ {stock['symbol']}: {result['message']}")
    
    # Show portfolio
    print(f"\n📊 Portfolio Status:")
    summary = engine.get_portfolio_summary()
    print(f"   Available Capital: ₹{summary['current_capital']:,.2f}")
    print(f"   Invested Capital: ₹{summary['invested_capital']:,.2f}")
    print(f"   Open Positions: {summary['open_positions_count']}")
    
    # Update prices
    print(f"\n📊 Market Update:")
    new_prices = {
        'NSE:RELIANCE-EQ': 2550,
        'NSE:TCS-EQ': 3480,
        'NSE:INFY-EQ': 1420,
    }
    engine.update_position_prices(new_prices)
    
    # Show positions
    print(f"\n📋 Current Positions:")
    positions = engine.get_open_positions()
    for pos in positions:
        print(f"   {pos['symbol']}:")
        print(f"      Entry: ₹{pos['entry_price']:,.2f} | Current: ₹{pos['current_price']:,.2f}")
        print(f"      P&L: ₹{pos['unrealized_pnl']:,.2f} ({pos['unrealized_pnl_percent']:.2f}%)")
    
    # Portfolio P&L
    summary = engine.get_portfolio_summary()
    print(f"\n💰 Total Unrealized P&L: ₹{summary['unrealized_pnl']:,.2f}")
    print(f"💰 Portfolio Value: ₹{summary['portfolio_value']:,.2f}")


def example_4_rejected_orders():
    """Example 4: Handling Rejected Orders"""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 4: Handling Rejected Orders")
    print("=" * 70)
    
    engine = PaperTradingEngine(
        initial_capital=50000,  # Small capital
        max_positions=2,
    )
    
    # Try to buy too much
    print(f"\n❌ Attempting to buy beyond capital limit:")
    result = engine.place_order(
        symbol='NSE:RELIANCE-EQ',
        side='BUY',
        quantity=50,  # 50 × 2500 = ₹1,25,000 (more than capital)
        price=2500,
    )
    print(f"   Status: {result['status']}")
    print(f"   Reason: {result['message']}")
    
    # Open first position
    print(f"\n✅ Opening first position:")
    result = engine.place_order(
        symbol='NSE:TCS-EQ',
        side='BUY',
        quantity=5,
        price=3500,
    )
    if result['status'] == 'SUCCESS':
        print(f"   Position 1 opened: NSE:TCS-EQ")
    
    # Try duplicate buy
    print(f"\n❌ Attempting duplicate BUY:")
    result = engine.place_order(
        symbol='NSE:TCS-EQ',
        side='BUY',
        quantity=5,
        price=3500,
    )
    print(f"   Status: {result['status']}")
    print(f"   Reason: {result['message']}")
    
    # Try to sell non-existent position
    print(f"\n❌ Attempting to sell without position:")
    result = engine.place_order(
        symbol='NSE:INFY-EQ',
        side='SELL',
        quantity=10,
        price=1400,
    )
    print(f"   Status: {result['status']}")
    print(f"   Reason: {result['message']}")


def example_5_performance_metrics():
    """Example 5: Performance Metrics and Analysis"""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 5: Performance Metrics and Analysis")
    print("=" * 70)
    
    engine = PaperTradingEngine(initial_capital=100000)
    
    # Simulate multiple trades
    trades_simulation = [
        {'symbol': 'NSE:RELIANCE-EQ', 'buy': 2500, 'sell': 2550, 'qty': 10},
        {'symbol': 'NSE:TCS-EQ', 'buy': 3500, 'sell': 3480, 'qty': 5},
        {'symbol': 'NSE:INFY-EQ', 'buy': 1400, 'sell': 1430, 'qty': 15},
        {'symbol': 'NSE:HDFCBANK-EQ', 'buy': 1600, 'sell': 1620, 'qty': 12},
        {'symbol': 'NSE:ICICIBANK-EQ', 'buy': 950, 'sell': 940, 'qty': 20},
    ]
    
    print(f"\n📊 Executing {len(trades_simulation)} trades:")
    for i, trade in enumerate(trades_simulation, 1):
        # BUY
        buy_result = engine.place_order(
            symbol=trade['symbol'],
            side='BUY',
            quantity=trade['qty'],
            price=trade['buy'],
        )
        
        if buy_result['status'] == 'SUCCESS':
            # Update price
            engine.update_position_prices({trade['symbol']: trade['sell']})
            
            # SELL
            sell_result = engine.place_order(
                symbol=trade['symbol'],
                side='SELL',
                quantity=trade['qty'],
                price=trade['sell'],
            )
            
            if sell_result['status'] == 'SUCCESS':
                pnl = sell_result['trade']['realized_pnl']
                emoji = "📈" if pnl > 0 else "📉"
                print(f"   {emoji} Trade {i}: {trade['symbol']} - P&L: ₹{pnl:,.2f}")
    
    # Show performance metrics
    print(f"\n📊 PERFORMANCE METRICS:")
    metrics = engine.get_performance_metrics()
    
    print(f"\n   Trading Activity:")
    print(f"      Total Trades: {metrics['total_trades']}")
    print(f"      Winning Trades: {metrics['winning_trades']}")
    print(f"      Losing Trades: {metrics['losing_trades']}")
    print(f"      Win Rate: {metrics['win_rate']:.2f}%")
    
    print(f"\n   P&L Analysis:")
    print(f"      Total Realized P&L: ₹{metrics['total_realized_pnl']:,.2f}")
    print(f"      Average Win: ₹{metrics['average_win']:,.2f}")
    print(f"      Average Loss: ₹{metrics['average_loss']:,.2f}")
    print(f"      Largest Win: ₹{metrics['largest_win']:,.2f}")
    print(f"      Largest Loss: ₹{metrics['largest_loss']:,.2f}")
    
    print(f"\n   Returns:")
    print(f"      Total Returns: {metrics['returns_percent']:.2f}%")
    print(f"      Total Brokerage: ₹{metrics['total_brokerage_paid']:,.2f}")
    
    # Portfolio summary
    summary = engine.get_portfolio_summary()
    print(f"\n   Final Portfolio:")
    print(f"      Initial Capital: ₹{summary['initial_capital']:,.2f}")
    print(f"      Final Capital: ₹{summary['current_capital']:,.2f}")
    print(f"      Portfolio Value: ₹{summary['portfolio_value']:,.2f}")
    print(f"      Net Profit: ₹{summary['portfolio_value'] - summary['initial_capital']:,.2f}")


def example_6_strategy_integration():
    """Example 6: Integration with Trading Strategy"""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 6: Integration with Trading Strategy")
    print("=" * 70)
    
    # Simple RSI-based strategy
    def generate_signals():
        """Simulate strategy signals"""
        return [
            {'symbol': 'NSE:RELIANCE-EQ', 'signal': 'BUY', 'price': 2500, 'rsi': 28},
            {'symbol': 'NSE:RELIANCE-EQ', 'signal': 'HOLD', 'price': 2520, 'rsi': 45},
            {'symbol': 'NSE:RELIANCE-EQ', 'signal': 'HOLD', 'price': 2550, 'rsi': 62},
            {'symbol': 'NSE:RELIANCE-EQ', 'signal': 'SELL', 'price': 2580, 'rsi': 74},
        ]
    
    engine = PaperTradingEngine(initial_capital=100000)
    
    print(f"\n📊 Running RSI Strategy (Oversold: <30, Overbought: >70)")
    print(f"\n{'Time':<8} {'Signal':<6} {'Price':<10} {'RSI':<6} {'Action':<30}")
    print("-" * 70)
    
    signals = generate_signals()
    for i, signal_data in enumerate(signals):
        symbol = signal_data['symbol']
        signal = signal_data['signal']
        price = signal_data['price']
        rsi = signal_data['rsi']
        
        action = "No action"
        
        if signal == 'BUY':
            result = engine.place_order(
                symbol=symbol,
                side='BUY',
                quantity=10,
                price=price,
            )
            if result['status'] == 'SUCCESS':
                action = f"✅ Bought 10 @ ₹{result['order']['executed_price']:,.2f}"
        
        elif signal == 'SELL':
            if engine.portfolio.has_position(symbol):
                result = engine.place_order(
                    symbol=symbol,
                    side='SELL',
                    quantity=10,
                    price=price,
                )
                if result['status'] == 'SUCCESS':
                    action = f"✅ Sold 10 @ ₹{result['order']['executed_price']:,.2f} | P&L: ₹{result['trade']['realized_pnl']:,.2f}"
        
        # Update position price
        if engine.portfolio.has_position(symbol):
            engine.update_position_prices({symbol: price})
            positions = engine.get_open_positions()
            if positions:
                unrealized = positions[0]['unrealized_pnl']
                if action == "No action":
                    action = f"Holding | Unrealized P&L: ₹{unrealized:,.2f}"
        
        print(f"T+{i:<6} {signal:<6} ₹{price:<8} {rsi:<6.1f} {action:<30}")
    
    # Final metrics
    print(f"\n📊 Strategy Performance:")
    metrics = engine.get_performance_metrics()
    print(f"   Trades Executed: {metrics['total_trades']}")
    print(f"   Total P&L: ₹{metrics['total_pnl']:,.2f}")
    print(f"   Returns: {metrics['returns_percent']:.2f}%")


def run_all_examples():
    """Run all examples"""
    example_1_simple_trade()
    example_2_stop_loss_target()
    example_3_multiple_positions()
    example_4_rejected_orders()
    example_5_performance_metrics()
    example_6_strategy_integration()
    
    print("\n\n" + "=" * 70)
    print("🎉 All examples completed successfully!")
    print("=" * 70)
    print("\nNext Steps:")
    print("1. Read PAPER_TRADING_GUIDE.md for detailed documentation")
    print("2. Integrate with your own trading strategy")
    print("3. Test with historical data (backtesting)")
    print("4. Test with live market data (paper trading)")
    print("5. Transition to live trading when confident")
    print("\n💡 Remember: Master paper trading before risking real capital!")


if __name__ == "__main__":
    run_all_examples()
