"""
Order management routes: Place, modify, cancel orders
"""
from fastapi import APIRouter, HTTPException, Body
from app.services.fyers import get_fyers_client
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/orders", tags=["Orders"])


class OrderRequest(BaseModel):
    """Order placement request model"""
    symbol: str
    qty: int
    side: int  # 1 for Buy, -1 for Sell
    type: int  # 1 for Market, 2 for Limit, 3 for Stop Loss, 4 for Stop Loss Market
    productType: str = "INTRADAY"  # INTRADAY, CNC, MARGIN
    limitPrice: Optional[float] = None
    stopPrice: Optional[float] = None
    validity: str = "DAY"  # DAY, IOC
    disclosedQty: int = 0
    offlineOrder: str = "False"
    stopLoss: Optional[float] = None
    takeProfit: Optional[float] = None


@router.post("/place")
def place_order(order: OrderRequest):
    """
    Place a new order.
    
    Order Types:
    - 1: Market Order
    - 2: Limit Order
    - 3: Stop Loss Order
    - 4: Stop Loss Market Order
    
    Product Types:
    - INTRADAY: Intraday (MIS equivalent)
    - CNC: Cash and Carry
    - MARGIN: Margin
    """
    try:
        fyers = get_fyers_client()
        
        # Build order data
        order_data = {
            "symbol": order.symbol,
            "qty": order.qty,
            "type": order.type,
            "side": order.side,
            "productType": order.productType,
            "limitPrice": order.limitPrice if order.limitPrice else 0,
            "stopPrice": order.stopPrice if order.stopPrice else 0,
            "validity": order.validity,
            "disclosedQty": order.disclosedQty,
            "offlineOrder": order.offlineOrder,
            "stopLoss": order.stopLoss if order.stopLoss else 0,
            "takeProfit": order.takeProfit if order.takeProfit else 0
        }
        
        response = fyers.place_order(data=order_data)
        
        if response.get("s") != "ok":
            error_msg = response.get("message", "Unknown error")
            error_code = response.get("code", "UNKNOWN")
            raise HTTPException(
                status_code=400,
                detail=f"Order placement failed [{error_code}]: {error_msg}"
            )
        
        return {
            "success": True,
            "order_id": response.get("id", ""),
            "message": response.get("message", "Order placed successfully"),
            "data": response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to place order: {str(e)}")


@router.get("")
def get_orders():
    """
    Get all orders.
    """
    try:
        fyers = get_fyers_client()
        
        response = fyers.orderbook()
        
        if response.get("s") != "ok":
            error_msg = response.get("message", "Unknown error")
            raise HTTPException(status_code=400, detail=f"Fyers API error: {error_msg}")
        
        orders = response.get("orderBook", [])
        
        return {
            "orders": orders,
            "count": len(orders)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")


@router.get("/{order_id}")
def get_order(order_id: str):
    """
    Get details of a specific order by ID.
    """
    try:
        fyers = get_fyers_client()
        
        response = fyers.orderbook()
        
        if response.get("s") != "ok":
            error_msg = response.get("message", "Unknown error")
            raise HTTPException(status_code=400, detail=f"Fyers API error: {error_msg}")
        
        orders = response.get("orderBook", [])
        
        # Find the specific order
        order = next((o for o in orders if str(o.get("id", "")) == str(order_id)), None)
        
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch order: {str(e)}")


@router.put("/{order_id}/modify")
def modify_order(
    order_id: str,
    limitPrice: Optional[float] = Body(None),
    stopPrice: Optional[float] = Body(None),
    qty: Optional[int] = Body(None),
    type: Optional[int] = Body(None)
):
    """
    Modify an existing order.
    """
    try:
        fyers = get_fyers_client()
        
        data = {
            "id": order_id
        }
        
        if limitPrice is not None:
            data["limitPrice"] = limitPrice
        if stopPrice is not None:
            data["stopPrice"] = stopPrice
        if qty is not None:
            data["qty"] = qty
        if type is not None:
            data["type"] = type
        
        response = fyers.modify_order(data=data)
        
        if response.get("s") != "ok":
            error_msg = response.get("message", "Unknown error")
            raise HTTPException(status_code=400, detail=f"Order modification failed: {error_msg}")
        
        return {
            "success": True,
            "message": response.get("message", "Order modified successfully"),
            "data": response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to modify order: {str(e)}")


@router.delete("/{order_id}")
def cancel_order(order_id: str):
    """
    Cancel an order.
    """
    try:
        fyers = get_fyers_client()
        
        data = {
            "id": order_id
        }
        
        response = fyers.cancel_order(data=data)
        
        if response.get("s") != "ok":
            error_msg = response.get("message", "Unknown error")
            raise HTTPException(status_code=400, detail=f"Order cancellation failed: {error_msg}")
        
        return {
            "success": True,
            "message": response.get("message", "Order cancelled successfully"),
            "data": response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel order: {str(e)}")


