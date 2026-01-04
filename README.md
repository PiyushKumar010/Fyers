# Fyers Trading Platform

A full-stack trading application built with React (frontend) and FastAPI (backend) that integrates with the Fyers API for real-time stock market data, technical indicators, and automated trading strategies.

## 🚀 Features

- **Real-time Market Data**: Live OHLC (Open, High, Low, Close) data from Fyers API
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Stochastic Oscillator, Supertrend, and more
- **Trend Analysis**: Automated trend detection (uptrend/downtrend/sideways)
- **Paper Trading**: Test strategies without real money
- **Automated Trading**: Execute strategies automatically
- **Strategy Builder**: Create custom trading strategies
- **Candlestick Patterns**: Detect bullish/bearish patterns
- **Market Status**: Real-time market open/close status
- **Authentication**: Secure OAuth2 authentication with Fyers

## 📁 Project Structure

```
fyers-ohlc/
├── fyers-frontend/          # React + Vite frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── api/           # API service layer
│   │   └── constants/     # Constants and config
│   ├── .env.example       # Environment variables template
│   └── package.json       # Node.js dependencies
│
├── fyers-ohlc-backend/     # FastAPI backend
│   ├── app/
│   │   ├── routes/        # API endpoints
│   │   ├── indicators/    # Technical indicators
│   │   ├── services/      # Business logic
│   │   ├── models/        # Database models
│   │   └── utils/         # Helper functions
│   ├── .env.example       # Environment variables template
│   └── requirements.txt   # Python dependencies
│
└── DEPLOYMENT.md          # Deployment guide
```

## 🛠️ Tech Stack

### Frontend
- React 18
- Vite 7
- React Router 6
- Recharts (charting)
- TailwindCSS (styling)
- date-fns (date handling)

### Backend
- FastAPI
- Python 3.12
- Fyers API v3
- MongoDB (database)
- Pandas (data processing)
- Uvicorn (ASGI server)

## 🚦 Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.12+
- MongoDB (local or MongoDB Atlas)
- Fyers API credentials ([Get them here](https://myapi.fyers.in/))

### Local Development Setup

#### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd fyers-ohlc
```

#### 2. Backend Setup
```bash
# Navigate to backend directory
cd fyers-ohlc-backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your credentials
```

**Configure .env file:**
```env
FYERS_CLIENT_ID=your_client_id
FYERS_SECRET_KEY=your_secret_key
FYERS_REDIRECT_URI=http://127.0.0.1:8000/auth/callback
MONGO_URI=mongodb://localhost:27017
DB_NAME=fyers_ohlc
```

**Start backend server:**
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend will run at: http://127.0.0.1:8000
- API Docs: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/health

#### 3. Frontend Setup
```bash
# Navigate to frontend directory (from project root)
cd fyers-frontend

# Install dependencies
npm install

# Copy environment template and configure
cp .env.example .env
# Default .env should work for local development
```

**Start frontend dev server:**
```bash
npm run dev
```

Frontend will run at: http://localhost:5173

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### Key Endpoints

#### Authentication
- `GET /auth/login` - Get Fyers login URL
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/status` - Check authentication status

#### Market Data
- `GET /ohlc/` - Get OHLC data for a symbol
- `GET /market/ltp` - Get last traded price
- `GET /market/quote` - Get detailed quote
- `GET /market/status` - Check market open/close status

#### Technical Analysis
- `GET /api/trend/analyze` - Analyze trend for a symbol
- `GET /api/trend/stochastic` - Get Stochastic Oscillator data
- `GET /signals/` - Get buy/sell signals

#### Trading
- `POST /paper-trading/orders/` - Place paper trade order
- `GET /paper-trading/portfolio/` - Get portfolio status
- `POST /automated-trading/start` - Start automated trading

## 🚀 Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed step-by-step deployment instructions for:
- **Frontend**: Vercel
- **Backend**: Render
- **Database**: MongoDB Atlas

Quick links:
- [Deploy to Vercel](https://vercel.com/new)
- [Deploy to Render](https://render.com)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)

## 🧪 Testing

### Backend Tests
```bash
cd fyers-ohlc-backend
python -m pytest app/tests/
```

### Frontend Tests
```bash
cd fyers-frontend
npm run test
```

## 📝 Environment Variables

### Frontend (.env)
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Backend (.env)
```env
# Fyers API
FYERS_CLIENT_ID=your_client_id
FYERS_SECRET_KEY=your_secret_key
FYERS_REDIRECT_URI=http://127.0.0.1:8000/auth/callback

# Database
MONGO_URI=mongodb://localhost:27017
DB_NAME=fyers_ohlc

# CORS (optional)
ALLOWED_ORIGINS=https://your-app.vercel.app

# Token Refresh (optional)
REFRESH_BUFFER_SECONDS=60
REFRESH_CHECK_INTERVAL=300
DISABLE_TOKEN_REFRESHER=false

# Data Storage (optional)
DISABLE_LIVE_DATA_STORAGE=true
LIVE_DATA_THRESHOLD_DAYS=1
```

## 🐛 Troubleshooting

### Common Issues

1. **Backend won't start**
   - Check if MongoDB is running
   - Verify environment variables in `.env`
   - Ensure virtual environment is activated

2. **Frontend can't connect to backend**
   - Verify `VITE_API_BASE_URL` in `.env`
   - Check if backend is running on port 8000
   - Check browser console for CORS errors

3. **Authentication fails**
   - Verify Fyers API credentials
   - Check redirect URI matches in Fyers dashboard
   - Ensure callback URL is accessible

4. **CORS errors**
   - Add frontend URL to backend CORS origins
   - For production, set `ALLOWED_ORIGINS` environment variable

## 📄 License

This project is private and proprietary.

## 🤝 Contributing

This is a private project. Contact the repository owner for contribution guidelines.

## 📧 Support

For issues and questions:
- Check [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment help
- Review API documentation at `/docs` endpoint
- Check application logs for error messages

## 🔐 Security

- Never commit `.env` files
- Keep API credentials secure
- Use environment variables for all secrets
- Enable HTTPS in production
- Restrict CORS to specific domains in production

## 🎯 Roadmap

- [ ] Add more technical indicators
- [ ] Implement backtesting engine
- [ ] Add real-time WebSocket streaming
- [ ] Mobile app (React Native)
- [ ] Advanced charting features
- [ ] Multi-timeframe analysis
- [ ] Portfolio optimization
- [ ] Risk management tools

---

**Built with ❤️ using React, FastAPI, and Fyers API**
