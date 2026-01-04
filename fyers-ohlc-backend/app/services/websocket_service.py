"""
Fyers WebSocket service for streaming live market data
"""
import asyncio
import json
import logging
from typing import Dict, List, Callable, Optional
from fyers_apiv3.FyersWebsocket import data_ws
from app.services.fyers import get_fyers_client
from app import database
from app.config import settings

logger = logging.getLogger(__name__)


class FyersWebSocketService:
    """
    Service to manage Fyers WebSocket connections and stream live data.
    """
    
    def __init__(self):
        self.data_socket: Optional[data_ws.FyersDataSocket] = None
        self.subscribed_symbols: List[str] = []
        self.callbacks: Dict[str, List[Callable]] = {}
        self.is_connected: bool = False
        self.access_token: Optional[str] = None
        
    def _get_access_token(self) -> str:
        """Get access token in format required by Fyers WebSocket"""
        tokens_collection = database.tokens_collection
        if tokens_collection is None:
            raise Exception("MongoDB not connected")
        
        token_doc = tokens_collection.find_one()
        if not token_doc or "access_token" not in token_doc:
            raise Exception("Fyers not authenticated")
        
        access_token = token_doc["access_token"]
        # Format: "appid:accesstoken"
        return f"{settings.FYERS_CLIENT_ID}:{access_token}"
    
    def _on_message(self, message: Dict):
        """Handle incoming WebSocket messages"""
        try:
            # Fyers sends data in different formats
            if isinstance(message, dict):
                # Symbol update format
                if "n" in message:  # Symbol name
                    symbol = message["n"]
                    data = {
                        "symbol": symbol,
                        "ltp": message.get("v", {}).get("lp", 0),
                        "volume": message.get("v", {}).get("volume", 0),
                        "change": message.get("v", {}).get("ch", 0),
                        "change_percent": message.get("v", {}).get("chp", 0),
                        "timestamp": message.get("v", {}).get("t", 0),
                        "open": message.get("v", {}).get("open_price", 0),
                        "high": message.get("v", {}).get("high_price", 0),
                        "low": message.get("v", {}).get("low_price", 0),
                        "close": message.get("v", {}).get("prev_close_price", 0)
                    }
                    
                    # Call registered callbacks
                    if symbol in self.callbacks:
                        for callback in self.callbacks[symbol]:
                            try:
                                callback(data)
                            except Exception as e:
                                logger.error(f"Error in callback for {symbol}: {e}")
                
                # Broadcast to all callbacks if no specific symbol match
                for symbol, callbacks in self.callbacks.items():
                    for callback in callbacks:
                        try:
                            callback(message)
                        except Exception as e:
                            logger.error(f"Error in general callback: {e}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    def _on_error(self, message: Dict):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {message}")
    
    def _on_close(self, message: Dict):
        """Handle WebSocket close"""
        logger.info(f"WebSocket closed: {message}")
        self.is_connected = False
    
    def _on_open(self):
        """Handle WebSocket open and subscribe to symbols"""
        logger.info("WebSocket connected")
        self.is_connected = True
        
        if self.subscribed_symbols:
            try:
                self.data_socket.subscribe(
                    symbols=self.subscribed_symbols,
                    data_type="SymbolUpdate"
                )
                self.data_socket.keep_running()
                logger.info(f"Subscribed to symbols: {self.subscribed_symbols}")
            except Exception as e:
                logger.error(f"Error subscribing to symbols: {e}")
    
    def connect(self):
        """Connect to Fyers WebSocket"""
        try:
            if self.is_connected:
                logger.warning("WebSocket already connected")
                return
            
            self.access_token = self._get_access_token()
            
            self.data_socket = data_ws.FyersDataSocket(
                access_token=self.access_token,
                log_path="",
                litemode=False,
                write_to_file=False,
                reconnect=True,
                on_connect=self._on_open,
                on_close=self._on_close,
                on_error=self._on_error,
                on_message=self._on_message
            )
            
            # Connect in a separate thread to avoid blocking
            import threading
            thread = threading.Thread(target=self.data_socket.connect, daemon=True)
            thread.start()
            
            logger.info("WebSocket connection initiated")
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from Fyers WebSocket"""
        try:
            if self.data_socket:
                self.data_socket.close_connection()
                self.is_connected = False
                logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {e}")
    
    def subscribe(self, symbol: str, callback: Callable):
        """
        Subscribe to a symbol and register a callback for updates.
        
        Args:
            symbol: Symbol to subscribe to (e.g., "NSE:RELIANCE-EQ")
            callback: Function to call when data is received
        """
        if symbol not in self.callbacks:
            self.callbacks[symbol] = []
        
        self.callbacks[symbol].append(callback)
        
        if symbol not in self.subscribed_symbols:
            self.subscribed_symbols.append(symbol)
            
            # If already connected, subscribe immediately
            if self.is_connected and self.data_socket:
                try:
                    self.data_socket.subscribe(
                        symbols=[symbol],
                        data_type="SymbolUpdate"
                    )
                    logger.info(f"Subscribed to {symbol}")
                except Exception as e:
                    logger.error(f"Error subscribing to {symbol}: {e}")
    
    def unsubscribe(self, symbol: str, callback: Optional[Callable] = None):
        """
        Unsubscribe from a symbol.
        
        Args:
            symbol: Symbol to unsubscribe from
            callback: Specific callback to remove (if None, removes all)
        """
        if symbol in self.callbacks:
            if callback:
                if callback in self.callbacks[symbol]:
                    self.callbacks[symbol].remove(callback)
            else:
                self.callbacks[symbol] = []
            
            if not self.callbacks[symbol]:
                del self.callbacks[symbol]
                if symbol in self.subscribed_symbols:
                    self.subscribed_symbols.remove(symbol)


# Global WebSocket service instance
_websocket_service: Optional[FyersWebSocketService] = None


def get_websocket_service() -> FyersWebSocketService:
    """Get or create the global WebSocket service instance"""
    global _websocket_service
    if _websocket_service is None:
        _websocket_service = FyersWebSocketService()
    return _websocket_service


