import { useState, useEffect } from "react";
import { getOrders, cancelOrder } from "../api/fyersApi";
import "./OrdersList.css";

export default function OrdersList() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getOrders();
      setOrders(response.orders || []);
    } catch (err) {
      setError(err.message || "Failed to fetch orders");
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const handleCancel = async (orderId) => {
    if (!window.confirm("Are you sure you want to cancel this order?")) {
      return;
    }

    try {
      await cancelOrder(orderId);
      await fetchOrders(); // Refresh list
    } catch (err) {
      alert(`Failed to cancel order: ${err.message}`);
    }
  };

  const getStatusColor = (status) => {
    const statusMap = {
      1: "#059669", // Pending
      2: "#2563eb", // Open
      3: "#dc2626", // Cancelled
      4: "#059669", // Executed
      5: "#f59e0b", // Rejected
    };
    return statusMap[status] || "#666";
  };

  const getStatusText = (status) => {
    const statusMap = {
      1: "Pending",
      2: "Open",
      3: "Cancelled",
      4: "Executed",
      5: "Rejected",
    };
    return statusMap[status] || "Unknown";
  };

  return (
    <div className="orders-list">
      <div className="orders-header">
        <h2>Orders</h2>
        <button onClick={fetchOrders} disabled={loading} className="refresh-button">
          {loading ? "⏳" : "🔄"} Refresh
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading && orders.length === 0 ? (
        <div className="loading">Loading orders...</div>
      ) : orders.length === 0 ? (
        <div className="empty-state">No orders found</div>
      ) : (
        <div className="table-wrapper">
          <table className="orders-table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Type</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Status</th>
                <th>Product</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.id}>
                  <td>{order.id}</td>
                  <td>{order.symbol}</td>
                  <td className={order.side === 1 ? "buy" : "sell"}>
                    {order.side === 1 ? "BUY" : "SELL"}
                  </td>
                  <td>{order.type === 1 ? "Market" : order.type === 2 ? "Limit" : "Stop"}</td>
                  <td>{order.qty}</td>
                  <td>₹{order.limitPrice || order.tradedPrice || "Market"}</td>
                  <td>
                    <span
                      className="status-badge"
                      style={{ backgroundColor: getStatusColor(order.status) }}
                    >
                      {getStatusText(order.status)}
                    </span>
                  </td>
                  <td>{order.productType}</td>
                  <td>
                    {order.status === 2 && (
                      <button
                        onClick={() => handleCancel(order.id)}
                        className="cancel-button"
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}


