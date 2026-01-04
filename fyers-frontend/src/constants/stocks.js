// Top 6 stocks for Market Overview
export const POPULAR_SYMBOLS = [
  { value: "NSE:RELIANCE-EQ", label: "RELIANCE", name: "Reliance Industries" },
  { value: "NSE:TCS-EQ", label: "TCS", name: "Tata Consultancy Services" },
  { value: "NSE:HDFCBANK-EQ", label: "HDFC Bank", name: "HDFC Bank" },
  { value: "NSE:INFY-EQ", label: "INFY", name: "Infosys" },
  { value: "NSE:ICICIBANK-EQ", label: "ICICI Bank", name: "ICICI Bank" },
  { value: "NSE:SBIN-EQ", label: "SBIN", name: "State Bank of India" },
];

// All available stocks for analysis
export const ALL_SYMBOLS = [
  { value: "NSE:RELIANCE-EQ", label: "RELIANCE" },
  { value: "NSE:TCS-EQ", label: "TCS" },
  { value: "NSE:HDFCBANK-EQ", label: "HDFC Bank" },
  { value: "NSE:INFY-EQ", label: "INFY" },
  { value: "NSE:ICICIBANK-EQ", label: "ICICI Bank" },
  { value: "NSE:SBIN-EQ", label: "SBIN" },
  { value: "NSE:HINDUNILVR-EQ", label: "HUL" },
  { value: "NSE:ITC-EQ", label: "ITC" },
  { value: "NSE:BHARTIARTL-EQ", label: "BHARTI ARTL" },
  { value: "NSE:KOTAKBANK-EQ", label: "KOTAK Bank" },
  { value: "NSE:LT-EQ", label: "L&T" },
  { value: "NSE:AXISBANK-EQ", label: "AXIS Bank" },
  { value: "NSE:BAJFINANCE-EQ", label: "BAJAJ Finance" },
  { value: "NSE:MARUTI-EQ", label: "MARUTI" },
  { value: "NSE:WIPRO-EQ", label: "WIPRO" },
  { value: "NSE:TITAN-EQ", label: "TITAN" },
  { value: "NSE:ASIANPAINT-EQ", label: "ASIAN PAINTS" },
  { value: "NSE:ULTRACEMCO-EQ", label: "ULTRATECH Cement" },
  { value: "NSE:NESTLEIND-EQ", label: "NESTLE" },
  { value: "NSE:SUNPHARMA-EQ", label: "SUN PHARMA" },
  { value: "NSE:ADANIPORTS-EQ", label: "ADANI PORTS" },
  { value: "NSE:POWERGRID-EQ", label: "POWER GRID" },
  { value: "NSE:NTPC-EQ", label: "NTPC" },
  { value: "NSE:TATASTEEL-EQ", label: "TATA STEEL" },
  { value: "NSE:JSWSTEEL-EQ", label: "JSW STEEL" },
  { value: "NSE:TATAMOTORS-EQ", label: "TATA MOTORS" },
  { value: "NSE:M&M-EQ", label: "M&M" },
  { value: "NSE:ONGC-EQ", label: "ONGC" },
  { value: "NSE:BPCL-EQ", label: "BPCL" },
  { value: "NSE:IOC-EQ", label: "IOC" },
];

// Helper function to normalize symbol format
export const normalizeSymbol = (sym) => {
  if (!sym) return "";
  const trimmed = sym.trim().toUpperCase();
  if (trimmed.includes(":")) return trimmed;
  return `NSE:${trimmed}-EQ`;
};
