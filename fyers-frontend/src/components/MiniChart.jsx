export default function MiniChart({ data }) {
  if (!data || data.length === 0) return null;

  const prices = data.map(d => d.close);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  
  const width = 120;
  const height = 40;
  const padding = 2;
  
  const points = prices.map((price, i) => {
    const x = (i / (prices.length - 1)) * (width - padding * 2) + padding;
    const y = height - ((price - min) / range) * (height - padding * 2) - padding;
    return `${x},${y}`;
  }).join(' ');

  const firstPrice = prices[0];
  const lastPrice = prices[prices.length - 1];
  const isPositive = lastPrice >= firstPrice;
  const color = isPositive ? '#10b981' : '#ef4444';

  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
