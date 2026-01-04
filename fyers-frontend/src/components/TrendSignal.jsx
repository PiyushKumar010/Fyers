import { useEffect, useState } from "react";
import { getTrendAnalyze, getStochastic } from "../api/fyersApi";
import "./TrendSignal.css";

// Lightweight client-side fallback when the backend returns no_data
function detectTrendLocal(candles) {
  if (!Array.isArray(candles) || candles.length < 5) return null;
  const len = candles.length - 1;
  const O = (i) => Number(candles[i]?.open);
  const H = (i) => Number(candles[i]?.high);
  const L = (i) => Number(candles[i]?.low);
  const C = (i) => Number(candles[i]?.close);

  try {
    const recentBullish = [0, 1, 2].every((j) => C(len - j) > O(len - j));
    const higherHighs = [2, 1, 0].every((j) => H(len - j) > H(len - j - 1));
    const higherLows = [2, 1, 0].every((j) => L(len - j) > L(len - j - 1));
    const priorBearish = [0, 1].every((j) => C(len - 3 - j) < O(len - 3 - j));
    const priorLowerHighs = [0, 1].every((j) => H(len - 2 - j) < H(len - 3 - j));
    const priorLowerLows = [0, 1].every((j) => L(len - 2 - j) < L(len - 3 - j));
    if (recentBullish && higherHighs && higherLows && priorBearish && priorLowerHighs && priorLowerLows) {
      return "Uptrend";
    }

    const recentBearish = [0, 1, 2].every((j) => C(len - j) < O(len - j));
    const lowerHighs = [2, 1, 0].every((j) => H(len - j) < H(len - j - 1));
    const lowerLows = [2, 1, 0].every((j) => L(len - j) < L(len - j - 1));
    const priorBullish = [0, 1].every((j) => C(len - 3 - j) > O(len - 3 - j));
    const priorHigherHighs = [0, 1].every((j) => H(len - 2 - j) > H(len - 3 - j));
    const priorHigherLows = [0, 1].every((j) => L(len - 2 - j) > L(len - 3 - j));
    if (recentBearish && lowerHighs && lowerLows && priorBullish && priorHigherHighs && priorHigherLows) {
      return "Downtrend";
    }
  } catch (e) {
    return null;
  }

  return null;
}

function computeStochLocal(candles, kPeriod = 14, dPeriod = 3) {
  if (!Array.isArray(candles) || candles.length < kPeriod) return { k: null, d: null };
  const highs = candles.map((c) => Number(c.high));
  const lows = candles.map((c) => Number(c.low));
  const closes = candles.map((c) => Number(c.close));

  const kValues = [];
  for (let i = kPeriod - 1; i < candles.length; i++) {
    const windowHigh = Math.max(...highs.slice(i - kPeriod + 1, i + 1));
    const windowLow = Math.min(...lows.slice(i - kPeriod + 1, i + 1));
    const denom = windowHigh - windowLow;
    const kVal = denom === 0 ? null : ((closes[i] - windowLow) / denom) * 100;
    kValues.push(kVal);
  }

  const latestK = kValues.length ? kValues[kValues.length - 1] : null;
  const recentKs = kValues.slice(-dPeriod).filter((v) => v !== null && !Number.isNaN(v));
  const dVal = recentKs.length ? recentKs.reduce((a, b) => a + b, 0) / recentKs.length : null;

  return { k: latestK, d: dVal };
}

export default function TrendSignal({ symbol, interval, duration = 5, ohlcData = [] }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [stochData, setStochData] = useState(null);

  useEffect(() => {
    let mounted = true;
    async function fetchData() {
      if (!symbol) return;
      setLoading(true);
      setError(null);
      try {
        const t = await getTrendAnalyze(symbol, interval, duration);
        const s = await getStochastic(symbol, interval, duration);
        if (!mounted) return;

        // Trend: if backend reports no data, clear to show neutral badge
        if (t && (t.note === "no_data" || t.status === "no_data")) {
          setTrendData(null);
        } else {
          setTrendData(t.data || t);
        }

        // Stochastic: pick last value when available, otherwise clear
        if (s && s.data && s.data.length) {
          setStochData(s.data[s.data.length - 1]);
        } else {
          setStochData(null);
        }

        // If API responded but yielded no usable data, fall back to local computation when possible
        if ((!t || t.status === "no_data" || t.note === "no_data") && Array.isArray(ohlcData) && ohlcData.length) {
          const trend = detectTrendLocal(ohlcData);
          const stoch = computeStochLocal(ohlcData);
          setTrendData(trend ? { trend } : null);
          setStochData(stoch);
        }
      } catch (e) {
        if (!mounted) return;
        // Client fallback using already-fetched OHLC candles if API says no_data or fails
        if (Array.isArray(ohlcData) && ohlcData.length) {
          const trend = detectTrendLocal(ohlcData);
          const stoch = computeStochLocal(ohlcData);
          setTrendData(trend ? { trend } : null);
          setStochData(stoch);
          setError(null);
        } else {
          setError(e.message || "Failed to load trend data");
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    fetchData();
    return () => (mounted = false);
  }, [symbol, interval, duration, ohlcData]);

  const renderBadge = (trend) => {
    if (!trend) return <span className="badge neutral">No clear trend</span>;
    // Ensure trend is a string
    const trendStr = typeof trend === 'string' ? trend : String(trend);
    if (trendStr.toLowerCase().includes("up")) return <span className="badge up">Uptrend</span>;
    if (trendStr.toLowerCase().includes("down")) return <span className="badge down">Downtrend</span>;
    return <span className="badge neutral">{trendStr}</span>;
  };

  return (
    <div className="trend-signal">
      <h3>Signal & Indicators</h3>
      {loading && <div className="ts-loading">Loading signals...</div>}
      {error && <div className="ts-error">Error: {error}</div>}

      {!loading && !error && (
        <div className="ts-grid">
          <div className="ts-card">
            <div className="ts-card-title">Trend</div>
            <div className="ts-card-value">
              {trendData ? renderBadge(
                typeof trendData === 'object' 
                  ? (trendData.trend || trendData.trend_label || 'No clear trend')
                  : trendData
              ) : <span className="badge neutral">—</span>}
            </div>
          </div>

          <div className="ts-card">
            <div className="ts-card-title">Stochastic %K</div>
            <div className="ts-card-value">
              {stochData && stochData.k != null ? Number(stochData.k).toFixed(2) : "—"}
            </div>
          </div>

          <div className="ts-card">
            <div className="ts-card-title">Stochastic %D</div>
            <div className="ts-card-value">
              {stochData && stochData.d != null ? Number(stochData.d).toFixed(2) : "—"}
            </div>
          </div>

          <div className="ts-card">
            <div className="ts-card-title">Momentum</div>
            <div className="ts-card-value">
              {stochData && stochData.k != null ? (
                stochData.k > 80 ? (
                  <span className="moment over">Overbought</span>
                ) : stochData.k < 20 ? (
                  <span className="moment under">Oversold</span>
                ) : (
                  <span className="moment neutral">Neutral</span>
                )
              ) : (
                "—"
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
