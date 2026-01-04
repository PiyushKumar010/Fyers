import { useMemo } from "react";
import {
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function CandlestickChart({ data }) {
  // Transform data for candlestick visualization
  const chartData = useMemo(() => {
    if (!Array.isArray(data) || data.length === 0) return [];

    return data
      .map((candle) => {
        const open = parseFloat(candle.open);
        const high = parseFloat(candle.high);
        const low = parseFloat(candle.low);
        const close = parseFloat(candle.close);

        // Validate data
        if (
          isNaN(open) || isNaN(high) || isNaN(low) || isNaN(close) ||
          open <= 0 || high <= 0 || low <= 0 || close <= 0 ||
          high < low
        ) {
          return null;
        }

        return {
          time: candle.time,
          open,
          high,
          low,
          close,
          // For bar chart representation
          range: [low, high],
          body: close >= open ? [open, close] : [close, open],
          color: close >= open ? "#26a69a" : "#ef5350",
        };
      })
      .filter(Boolean);
  }, [data]);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div
          style={{
            backgroundColor: "rgba(255, 255, 255, 0.95)",
            padding: "10px",
            border: "1px solid #ccc",
            borderRadius: "4px",
          }}
        >
          <p style={{ margin: 0, fontWeight: "bold" }}>{data.time}</p>
          <p style={{ margin: "4px 0", color: "#666" }}>
            Open: <strong>{data.open.toFixed(2)}</strong>
          </p>
          <p style={{ margin: "4px 0", color: "#666" }}>
            High: <strong>{data.high.toFixed(2)}</strong>
          </p>
          <p style={{ margin: "4px 0", color: "#666" }}>
            Low: <strong>{data.low.toFixed(2)}</strong>
          </p>
          <p style={{ margin: "4px 0", color: "#666" }}>
            Close: <strong>{data.close.toFixed(2)}</strong>
          </p>
        </div>
      );
    }
    return null;
  };

  if (!chartData || chartData.length === 0) {
    return (
      <div
        style={{
          width: "100%",
          height: "500px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#999",
        }}
      >
        No data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={500}>
      <ComposedChart
        data={chartData}
        margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
        <XAxis
          dataKey="time"
          tick={{ fontSize: 12 }}
          tickFormatter={(value) => {
            const date = new Date(value);
            return `${date.getHours()}:${String(date.getMinutes()).padStart(2, "0")}`;
          }}
        />
        <YAxis
          domain={["auto", "auto"]}
          tick={{ fontSize: 12 }}
          tickFormatter={(value) => value.toFixed(2)}
        />
        <Tooltip content={<CustomTooltip />} />
        
        {/* Wick (High-Low range) */}
        <Bar
          dataKey="range"
          fill="#8884d8"
          shape={(props) => {
            const { x, y, width, height, payload } = props;
            const centerX = x + width / 2;
            return (
              <line
                x1={centerX}
                y1={y}
                x2={centerX}
                y2={y + height}
                stroke="#666"
                strokeWidth={1}
              />
            );
          }}
        />
        
        {/* Body (Open-Close) */}
        <Bar
          dataKey="body"
          fill="#8884d8"
          shape={(props) => {
            const { x, y, width, height, payload } = props;
            return (
              <rect
                x={x}
                y={y}
                width={width}
                height={height}
                fill={payload.color}
                stroke={payload.color}
                strokeWidth={1}
              />
            );
          }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
