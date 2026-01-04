"""
WebSocket routes for streaming live market data
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.websocket_service import get_websocket_service
from app.services.fyers import normalize_symbol
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/market")
async def market_websocket(
    websocket: WebSocket,
    symbols: str = Query(..., description="Comma-separated symbols to subscribe to")
):
    """
    WebSocket endpoint for streaming live market data (LTP, quotes).
    Subscribes to Fyers WebSocket and forwards tick data to clients.
    """
    await websocket.accept()
    
    try:
        # Parse symbols
        symbol_list = [s.strip() for s in symbols.split(",")]
        normalized_symbols = []
        
        for symbol in symbol_list:
            try:
                normalized = normalize_symbol(symbol)
                normalized_symbols.append(normalized)
            except Exception as e:
                await websocket.send_json({
                    "error": f"Invalid symbol {symbol}: {str(e)}"
                })
                continue
        
        if not normalized_symbols:
            await websocket.send_json({
                "error": "No valid symbols provided"
            })
            await websocket.close()
            return
        
        # Get WebSocket service
        ws_service = get_websocket_service()
        
        # Store client connections per symbol
        client_callbacks = {}
        
        def create_callback(symbol: str):
            """Create a callback function for a symbol"""
            def callback(data: dict):
                try:
                    # Send data to WebSocket client
                    asyncio.create_task(
                        websocket.send_json({
                            "symbol": symbol,
                            "data": data,
                            "type": "tick"
                        })
                    )
                except Exception as e:
                    logger.error(f"Error sending data to client for {symbol}: {e}")
            return callback
        
        # Subscribe to each symbol
        for symbol in normalized_symbols:
            callback = create_callback(symbol)
            ws_service.subscribe(symbol, callback)
            client_callbacks[symbol] = callback
        
        # Connect WebSocket if not already connected
        if not ws_service.is_connected:
            try:
                ws_service.connect()
                await asyncio.sleep(2)  # Wait for connection to establish
            except Exception as e:
                await websocket.send_json({
                    "error": f"Failed to connect to Fyers WebSocket: {str(e)}"
                })
                await websocket.close()
                return
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Subscribed to symbols",
            "symbols": normalized_symbols
        })
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages (ping/pong or unsubscribe)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "unsubscribe":
                    symbol = message.get("symbol")
                    if symbol and symbol in client_callbacks:
                        ws_service.unsubscribe(symbol, client_callbacks[symbol])
                        del client_callbacks[symbol]
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling client message: {e}")
                break
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "error": f"WebSocket error: {str(e)}"
            })
        except:
            pass
    finally:
        # Cleanup: unsubscribe all symbols
        try:
            ws_service = get_websocket_service()
            for symbol, callback in client_callbacks.items():
                ws_service.unsubscribe(symbol, callback)
        except:
            pass
        
        try:
            await websocket.close()
        except:
            pass


import asyncio


