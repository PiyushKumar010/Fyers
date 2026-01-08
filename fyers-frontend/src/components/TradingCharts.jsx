import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

// Custom colors for charts
const COLORS = ['#22c55e', '#ef4444', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899'];
const WIN_COLOR = '#22c55e';
const LOSS_COLOR = '#ef4444';

export function WinLossDistributionChart({ performance }) {
  if (!performance) return null;

  const data = [
    { name: 'Winning Trades', value: performance.winning_trades, color: WIN_COLOR },
    { name: 'Losing Trades', value: performance.losing_trades, color: LOSS_COLOR },
  ];

  // Filter out zero values
  const filteredData = data.filter(item => item.value > 0);

  if (filteredData.length === 0) {
    return <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>No trades executed yet</div>;
  }

  const renderLabel = (entry) => {
    const percent = ((entry.value / (performance.winning_trades + performance.losing_trades)) * 100).toFixed(1);
    return `${entry.name}: ${entry.value} (${percent}%)`;
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={filteredData}
          cx="50%"
          cy="50%"
          labelLine={true}
          label={renderLabel}
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
        >
          {filteredData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip formatter={(value) => `${value} trades`} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function StrategySignalsChart({ signals }) {
  if (!signals || !signals.signal_breakdown) return null;

  const data = Object.entries(signals.signal_breakdown).map(([strategy, stats]) => ({
    name: strategy,
    Buy: stats.BUY || 0,
    Sell: stats.SELL || 0,
    Total: stats.total || 0,
  }));

  if (data.length === 0 || data.every(d => d.Total === 0)) {
    return <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>No signals generated yet</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
        <XAxis dataKey="name" stroke="#666" />
        <YAxis stroke="#666" />
        <Tooltip 
          contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: '4px' }}
        />
        <Legend />
        <Bar dataKey="Buy" fill="#22c55e" />
        <Bar dataKey="Sell" fill="#ef4444" />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function PortfolioPerformanceChart({ portfolio }) {
  if (!portfolio) return null;

  const data = [
    {
      name: 'Initial Capital',
      value: portfolio.initial_capital,
    },
    {
      name: 'Final Value',
      value: portfolio.final_value,
    },
  ];

  const maxValue = Math.max(portfolio.initial_capital, portfolio.final_value);
  const minValue = Math.min(portfolio.initial_capital, portfolio.final_value);

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
        <XAxis type="number" stroke="#666" domain={[0, maxValue * 1.1]} />
        <YAxis type="category" dataKey="name" stroke="#666" width={100} />
        <Tooltip 
          formatter={(value) => `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`}
          contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: '4px' }}
        />
        <Bar dataKey="value" fill="#3b82f6">
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={index === 0 ? '#94a3b8' : (portfolio.total_pnl >= 0 ? '#22c55e' : '#ef4444')} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ProfitLossBreakdownChart({ portfolio }) {
  if (!portfolio) return null;

  const data = [
    { name: 'Realized P&L', value: Math.abs(portfolio.realized_pnl), type: portfolio.realized_pnl >= 0 ? 'profit' : 'loss' },
    { name: 'Unrealized P&L', value: Math.abs(portfolio.unrealized_pnl), type: portfolio.unrealized_pnl >= 0 ? 'profit' : 'loss' },
    { name: 'Charges', value: Math.abs(portfolio.total_charges || 0), type: 'loss' },
  ];

  const chartData = [
    { name: 'Realized P&L', value: portfolio.realized_pnl },
    { name: 'Unrealized P&L', value: portfolio.unrealized_pnl },
    { name: 'Charges', value: -(portfolio.total_charges || 0) },
  ];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
        <XAxis dataKey="name" stroke="#666" />
        <YAxis stroke="#666" />
        <Tooltip 
          formatter={(value) => `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`}
          contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: '4px' }}
        />
        <Bar dataKey="value" fill="#3b82f6">
          {chartData.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={entry.value >= 0 ? '#22c55e' : '#ef4444'} 
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function TradePerformanceChart({ performance }) {
  if (!performance) return null;

  const data = [
    { name: 'Average Win', value: performance.avg_win, color: WIN_COLOR },
    { name: 'Average Loss', value: Math.abs(performance.avg_loss), color: LOSS_COLOR },
  ].filter(item => item.value > 0);

  if (data.length === 0) {
    return <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>No trade data available</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
        <XAxis dataKey="name" stroke="#666" />
        <YAxis stroke="#666" />
        <Tooltip 
          formatter={(value) => `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`}
          contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: '4px' }}
        />
        <Bar dataKey="value" fill="#3b82f6">
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
