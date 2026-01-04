import { useState } from "react";
import { placeOrder } from "../api/fyersApi";
import "./OrderPlacement.css";

const ORDER_TYPES = [
  { value: 1, label: "Market" },
  { value: 2, label: "Limit" },
  { value: 3, label: "Stop Loss" },
  { value: 4, label: "Stop Loss Market" },
];

const PRODUCT_TYPES = [
  { value: "INTRADAY", label: "Intraday (MIS)" },
  { value: "CNC", label: "CNC" },
  { value: "MARGIN", label: "Margin" },
];

export default function OrderPlacement({ symbol, onOrderPlaced }) {
  const [orderData, setOrderData] = useState({
    symbol: symbol || "",
    qty: 1,
    side: 1, // 1 for Buy, -1 for Sell
    type: 1, // Market order
    productType: "INTRADAY",
    limitPrice: "",
    stopPrice: "",
    validity: "DAY",
    stopLoss: "",
    takeProfit: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const payload = {
        ...orderData,
        qty: parseInt(orderData.qty),
        limitPrice: orderData.limitPrice ? parseFloat(orderData.limitPrice) : null,
        stopPrice: orderData.stopPrice ? parseFloat(orderData.stopPrice) : null,
        stopLoss: orderData.stopLoss ? parseFloat(orderData.stopLoss) : null,
        takeProfit: orderData.takeProfit ? parseFloat(orderData.takeProfit) : null,
      };

      const result = await placeOrder(payload);
      setSuccess(`Order placed successfully! Order ID: ${result.order_id}`);
      
      // Reset form
      setOrderData({
        symbol: symbol || "",
        qty: 1,
        side: 1,
        type: 1,
        productType: "INTRADAY",
        limitPrice: "",
        stopPrice: "",
        validity: "DAY",
        stopLoss: "",
        takeProfit: "",
      });

      if (onOrderPlaced) {
        onOrderPlaced(result);
      }
    } catch (err) {
      setError(err.message || "Failed to place order");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="order-placement">
      <h2>Place Order</h2>
      <form onSubmit={handleSubmit} className="order-form">
        <div className="form-row">
          <div className="form-group">
            <label>Symbol</label>
            <input
              type="text"
              value={orderData.symbol}
              onChange={(e) => setOrderData({ ...orderData, symbol: e.target.value.toUpperCase() })}
              placeholder="NSE:RELIANCE-EQ"
              required
            />
          </div>

          <div className="form-group">
            <label>Quantity</label>
            <input
              type="number"
              value={orderData.qty}
              onChange={(e) => setOrderData({ ...orderData, qty: e.target.value })}
              min="1"
              required
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Side</label>
            <select
              value={orderData.side}
              onChange={(e) => setOrderData({ ...orderData, side: parseInt(e.target.value) })}
            >
              <option value={1}>Buy</option>
              <option value={-1}>Sell</option>
            </select>
          </div>

          <div className="form-group">
            <label>Order Type</label>
            <select
              value={orderData.type}
              onChange={(e) => setOrderData({ ...orderData, type: parseInt(e.target.value) })}
            >
              {ORDER_TYPES.map((ot) => (
                <option key={ot.value} value={ot.value}>
                  {ot.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Product Type</label>
            <select
              value={orderData.productType}
              onChange={(e) => setOrderData({ ...orderData, productType: e.target.value })}
            >
              {PRODUCT_TYPES.map((pt) => (
                <option key={pt.value} value={pt.value}>
                  {pt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Validity</label>
            <select
              value={orderData.validity}
              onChange={(e) => setOrderData({ ...orderData, validity: e.target.value })}
            >
              <option value="DAY">DAY</option>
              <option value="IOC">IOC</option>
            </select>
          </div>
        </div>

        {(orderData.type === 2 || orderData.type === 3) && (
          <div className="form-group">
            <label>Limit Price</label>
            <input
              type="number"
              step="0.01"
              value={orderData.limitPrice}
              onChange={(e) => setOrderData({ ...orderData, limitPrice: e.target.value })}
              placeholder="0.00"
            />
          </div>
        )}

        {(orderData.type === 3 || orderData.type === 4) && (
          <div className="form-group">
            <label>Stop Price</label>
            <input
              type="number"
              step="0.01"
              value={orderData.stopPrice}
              onChange={(e) => setOrderData({ ...orderData, stopPrice: e.target.value })}
              placeholder="0.00"
            />
          </div>
        )}

        <div className="form-row">
          <div className="form-group">
            <label>Stop Loss (Optional)</label>
            <input
              type="number"
              step="0.01"
              value={orderData.stopLoss}
              onChange={(e) => setOrderData({ ...orderData, stopLoss: e.target.value })}
              placeholder="0.00"
            />
          </div>

          <div className="form-group">
            <label>Take Profit (Optional)</label>
            <input
              type="number"
              step="0.01"
              value={orderData.takeProfit}
              onChange={(e) => setOrderData({ ...orderData, takeProfit: e.target.value })}
              placeholder="0.00"
            />
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <button type="submit" disabled={loading} className="submit-button">
          {loading ? "Placing Order..." : "Place Order"}
        </button>
      </form>
    </div>
  );
}


