from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes import (
    health, auth, ohlc, market, 
    websocket, strategies, signals, candlestick, strategy, trend_analysis,
    advanced_strategies, automated_trading
)
from app.services import token_refresher

app = FastAPI(
    title="Fyers OHLC API",
    description="API for fetching and caching OHLC (Open, High, Low, Close) stock market data from Fyers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
import os
from dotenv import load_dotenv

load_dotenv()

# Get allowed origins from environment variable or use defaults
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
origins = [
    "http://localhost:5173",  # React dev server (Vite default)
    "http://127.0.0.1:5173",
    "http://localhost:5174",  # Alternative Vite port
    "http://127.0.0.1:5174",
    "http://localhost:3000",  # Alternative React dev server
    "http://127.0.0.1:3000",
] + [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(ohlc.router)
app.include_router(market.router)
app.include_router(websocket.router)
app.include_router(signals.router)
app.include_router(strategies.router)
app.include_router(candlestick.router, prefix="/api/candlestick", tags=["candlestick"])
app.include_router(strategy.router, prefix="/api/strategy", tags=["strategy"])
app.include_router(trend_analysis.router)
app.include_router(advanced_strategies.router)
app.include_router(automated_trading.router)


@app.on_event("startup")
async def startup_event():
    # Start background token refresher to keep access token valid automatically
    try:
        if getattr(token_refresher, "_task", None) is None and not token_refresher.__dict__.get('DISABLE_CHECK', False):
            # allow disabling via settings for debugging
            from app.config import settings
            if not getattr(settings, 'DISABLE_TOKEN_REFRESHER', False):
                print("[startup] starting token_refresher.start_refresher()")
                token_refresher.start_refresher()
                print("[startup] token_refresher.start_refresher() returned")
            else:
                print("[startup] token_refresher disabled by settings")
        else:
            print("[startup] token_refresher already present or disabled via attribute")
    except Exception:
        import traceback
        print("[startup] token_refresher.start_refresher() raised exception:")
        traceback.print_exc()
        # continue startup even if refresher fails
        pass


@app.on_event("shutdown")
async def shutdown_event():
    # Stop background refresher gracefully
    try:
        print("[shutdown] stopping token refresher")
        await token_refresher.stop_refresher()
        print("[shutdown] token refresher stopped")
    except Exception:
        import traceback
        print("[shutdown] token_refresher.stop_refresher() raised:")
        traceback.print_exc()
        pass


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return JSONResponse({
        "message": "Fyers OHLC API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "auth": "/auth/login",
            "ohlc": "/ohlc",
            "market": "/market",
            "websocket": "/ws/market",
            "signals": "/signals",
            "automated_trading": "/api/automated-trading"
        }
    })


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "path": str(request.url)
        }
    )