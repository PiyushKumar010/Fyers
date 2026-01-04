const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function getOhlc(symbol, from_date, to_date, resolution = "5") {
  try {
    const response = await fetch(
      `${BASE_URL}/ohlc/?symbol=${symbol}&from_date=${from_date}&to_date=${to_date}&resolution=${resolution}`
    );
    
    const payload = await response.json().catch(() => (null));

    if (!response.ok) {
      const errorData = payload || {};
      if (response.status === 401) {
        const detail = (errorData.detail || "Authentication required");
        throw new Error(`AUTH_REQUIRED: ${detail}`);
      }
      const detail = (errorData.detail || "").toLowerCase();

      // Known no-data messages from backend / Fyers — return an empty payload instead of throwing
      if (detail.includes("no ohlc data") || detail.includes("no_data") || (errorData.note && errorData.note === "no_data")) {
        return { source: errorData.source || "fyers", data: [], count: 0, note: "no_data" };
      }

      throw new Error(errorData.detail || `HTTP ${response.status}: Failed to fetch OHLC data`);
    }

    // If OK but payload indicates empty data, normalize it
    if (payload && Array.isArray(payload.data) && payload.data.length === 0) {
      return { source: payload.source || "fyers", data: [], count: 0, note: payload.note || "no_data" };
    }

    return payload;
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
}

export async function getLoginUrl() {
  try {
    const response = await fetch(`${BASE_URL}/auth/login`);
    if (!response.ok) throw new Error("Failed to get login URL");
    return await response.json();
  } catch (error) {
    console.error("Auth Error:", error);
    throw error;
  }
}

export async function getAuthStatus() {
  try {
    const response = await fetch(`${BASE_URL}/auth/status`);
    if (!response.ok) throw new Error("Failed to get auth status");
    return await response.json();
  } catch (error) {
    console.error("Auth status error:", error);
    return { authenticated: false, message: "unknown" };
  }
}

export async function checkHealth() {
  try {
    const response = await fetch(`${BASE_URL}/health`);
    return await response.json();
  } catch (error) {
    console.error("Health check failed:", error);
    return { status: "error" };
  }
}

export async function getMarketStatus() {
  try {
    const response = await fetch(`${BASE_URL}/market/status`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error("Market status error:", error);
    return { is_open: false, status: "unknown", reason: "API error" };
  }
}

// Market Data APIs
export async function getLtp(symbol) {
  try {
    const response = await fetch(`${BASE_URL}/market/ltp?symbol=${encodeURIComponent(symbol)}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error("LTP Error:", error);
    throw error;
  }
}

// Trend & Indicator APIs
export async function getTrendAnalyze(symbol, interval = "5", duration = 5) {
  try {
    const url = `${BASE_URL}/api/trend/analyze?symbol=${encodeURIComponent(symbol)}&interval=${encodeURIComponent(interval)}&duration=${encodeURIComponent(duration)}`;
    const response = await fetch(url);
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      const detail = (err.detail || "").toLowerCase();
      // Normalize no-data responses so UI can show a friendly empty state
      if (detail.includes("no_data") || detail.includes("no data")) {
        return { status: "no_data", note: "no_data", data: null };
      }
      throw new Error(err.detail || `HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("getTrendAnalyze error:", error);
    throw error;
  }
}

export async function getStochastic(symbol, interval = "5", duration = 5, k_period = 14, d_period = 3) {
  try {
    const url = `${BASE_URL}/api/trend/stochastic?symbol=${encodeURIComponent(symbol)}&interval=${encodeURIComponent(interval)}&duration=${encodeURIComponent(duration)}&k_period=${k_period}&d_period=${d_period}`;
    const response = await fetch(url);
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      const detail = (err.detail || "").toLowerCase();
      if (detail.includes("no_data") || detail.includes("no data") || response.status === 404) {
        return { status: "no_data", note: "no_data", data: [] };
      }
      throw new Error(err.detail || `HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("getStochastic error:", error);
    throw error;
  }
}

export async function getQuote(symbol) {
  try {
    const response = await fetch(`${BASE_URL}/market/quote?symbol=${encodeURIComponent(symbol)}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error("Quote Error:", error);
    throw error;
  }
}

export async function getQuotes(symbols) {
  try {
    const symbolStr = Array.isArray(symbols) ? symbols.join(",") : symbols;
    const response = await fetch(`${BASE_URL}/market/quotes?symbols=${encodeURIComponent(symbolStr)}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error("Quotes Error:", error);
    throw error;
  }
}

// Order APIs
export async function placeOrder(orderData) {
  try {
    const response = await fetch(`${BASE_URL}/orders/place`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(orderData),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Order placement failed");
    }
    return await response.json();
  } catch (error) {
    console.error("Place Order Error:", error);
    throw error;
  }
}

export async function getOrders() {
  try {
    const response = await fetch(`${BASE_URL}/orders`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error("Get Orders Error:", error);
    throw error;
  }
}

export async function cancelOrder(orderId) {
  try {
    const response = await fetch(`${BASE_URL}/orders/${orderId}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Order cancellation failed");
    }
    return await response.json();
  } catch (error) {
    console.error("Cancel Order Error:", error);
    throw error;
  }
}

// Positions APIs
export async function getPositions() {
  try {
    const response = await fetch(`${BASE_URL}/positions`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error("Get Positions Error:", error);
    throw error;
  }
}

export async function getHoldings() {
  try {
    const response = await fetch(`${BASE_URL}/positions/holdings`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error("Get Holdings Error:", error);
    throw error;
  }
}
