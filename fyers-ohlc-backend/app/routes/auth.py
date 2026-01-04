from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.responses import RedirectResponse
from fyers_apiv3 import fyersModel
from app.config import settings
from app import database
from datetime import datetime
from app.services import fyers as fyers_service
import os

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/test-callback")
def test_callback(request: Request):
    """
    Test endpoint to verify redirect URI is accessible.
    Visit: http://127.0.0.1:8000/auth/test-callback
    """
    return {
        "status": "ok",
        "message": "Callback endpoint is accessible!",
        "url": str(request.url),
        "query_params": dict(request.query_params),
        "redirect_uri_configured": settings.FYERS_REDIRECT_URI
    }


@router.get("/login")
def fyers_login():
    """
    Generate Fyers OAuth login URL.
    Returns a URL that the user should visit to authenticate.
    """
    try:
        if not settings.FYERS_CLIENT_ID or not settings.FYERS_REDIRECT_URI:
            raise HTTPException(
                status_code=500,
                detail="Fyers credentials not configured. Please check environment variables."
            )

        print(f"[AUTH] Generating login URL with:")
        print(f"  Client ID: {settings.FYERS_CLIENT_ID}")
        print(f"  Redirect URI: {settings.FYERS_REDIRECT_URI}")

        session = fyersModel.SessionModel(
            client_id=settings.FYERS_CLIENT_ID,
            redirect_uri=settings.FYERS_REDIRECT_URI,
            response_type="code",
            state="state123"
        )
        login_url = session.generate_authcode()
        
        print(f"[AUTH] Generated login URL: {login_url}")
        
        return {
            "login_url": login_url,
            "message": "Visit the login_url to authenticate with Fyers"
        }
    except Exception as e:
        print(f"[AUTH] Error generating login URL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate login URL: {str(e)}"
        )


@router.get("/callback")
def fyers_callback(
    request: Request,
    auth_code: str = Query(None, description="Authorization code from Fyers OAuth callback"), 
    code: str = Query(None, description="Alternative param name for auth code"),
    error: str = Query(None),
    error_description: str = Query(None),
    state: str = Query(None, description="State parameter for CSRF protection")
):
    """
    Handle Fyers OAuth callback.
    Exchanges authorization code for access token and stores it in MongoDB.
    Redirects to frontend with success/error status.
    """
    # Get frontend URL from environment or ALLOWED_ORIGINS, fallback to localhost
    frontend_url = os.getenv("FRONTEND_URL")
    if not frontend_url:
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
        frontend_url = allowed_origins.split(",")[0].strip() if allowed_origins else "http://localhost:5173"
    
    # Use whichever code parameter was provided
    actual_code = auth_code or code
    
    # Log ALL query parameters to debug
    print(f"\n{'='*60}")
    print(f"[AUTH CALLBACK] Received callback at {datetime.now()}")
    print(f"{'='*60}")
    print(f"Full URL: {request.url}")
    print(f"Query Params: {dict(request.query_params)}")
    print(f"  auth_code: {auth_code}")
    print(f"  code: {code}")
    print(f"  actual_code (merged): {actual_code}")
    print(f"  error: {error}")
    print(f"  error_description: {error_description}")
    print(f"  state: {state}")
    print(f"{'='*60}\n")
    
    # Check if Fyers returned an error
    if error:
        error_msg = error_description or error
        print(f"[AUTH CALLBACK] Fyers returned error: {error_msg}")
        return RedirectResponse(
            url=f"{frontend_url}/?auth=error&message=Fyers+error:+{error_msg}"
        )
    
    # Check if auth_code is missing
    if not actual_code:
        print(f"[AUTH CALLBACK] No auth_code received")
        return RedirectResponse(
            url=f"{frontend_url}/?auth=error&message=No+authorization+code+received"
        )
    
    try:
        if not settings.FYERS_CLIENT_ID or not settings.FYERS_SECRET_KEY:
            print(f"[AUTH CALLBACK] Missing credentials")
            return RedirectResponse(
                url=f"{frontend_url}/?auth=error&message=Configuration+error"
            )

        print(f"[AUTH CALLBACK] Creating session to exchange code for token")
        session = fyersModel.SessionModel(
            client_id=settings.FYERS_CLIENT_ID,
            secret_key=settings.FYERS_SECRET_KEY,
            redirect_uri=settings.FYERS_REDIRECT_URI,
            response_type="code",
            grant_type="authorization_code"
        )

        session.set_token(actual_code)
        print(f"[AUTH CALLBACK] Calling generate_token()...")
        response = session.generate_token()
        print(f"[AUTH CALLBACK] Token response: {response}")

        if "access_token" not in response:
            error_msg = response.get("message", "Unknown error")
            error_code = response.get("code", "UNKNOWN")
            print(f"[AUTH CALLBACK] Token generation failed: {error_code} - {error_msg}")
            return RedirectResponse(
                url=f"{frontend_url}/?auth=error&message=Authentication+failed:+{error_msg}"
            )

        tokens_collection = database.tokens_collection
        if tokens_collection is None:
            print(f"[AUTH CALLBACK] Database not available")
            return RedirectResponse(
                url=f"{frontend_url}/?auth=error&message=Database+error"
            )

        # Remove old tokens and store new one, adding obtained timestamp
        token_entry = dict(response)
        token_entry["obtained_at"] = datetime.utcnow().timestamp()

        print(f"[AUTH CALLBACK] Preparing to store token entry: {token_entry}")
        tokens_collection.delete_many({})
        result = tokens_collection.insert_one(token_entry)
        print(f"[AUTH CALLBACK] Token stored successfully! Insert ID: {result.inserted_id}")
        
        # Verify it was stored
        verify_token = tokens_collection.find_one()
        print(f"[AUTH CALLBACK] Verification - token in DB: {verify_token}")

        # Redirect to frontend with success message
        return RedirectResponse(
            url=f"{frontend_url}/?auth=success&message=Authentication+successful"
        )
    except Exception as e:
        print(f"[AUTH CALLBACK] Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(
            url=f"{frontend_url}/?auth=error&message={str(e)}"
        )


@router.get("/status")
def auth_status():
    """
    Check current authentication status.
    Returns whether a valid access token exists in the database and actually works.
    """
    tokens_collection = database.tokens_collection
    if tokens_collection is None:
        return {
            "authenticated": False,
            "message": "MongoDB not connected",
            "debug": "db_unavailable"
        }

    token_doc = tokens_collection.find_one()
    print(f"[AUTH STATUS] Token doc: {token_doc}")
    
    if not token_doc or "access_token" not in token_doc:
        return {
            "authenticated": False,
            "message": "No access token found. Please authenticate.",
            "debug": "no_token"
        }
    
    # Actually test if the token works by trying to create a client
    try:
        from app.services.fyers import get_fyers_client
        fyers = get_fyers_client()
        # Try a simple API call to verify token works
        # Use profile() as a lightweight test
        response = fyers.get_profile()
        print(f"[AUTH STATUS] Profile check response: {response}")
        
        if response.get("s") == "ok":
            return {
                "authenticated": True,
                "message": "Valid and working access token",
                "debug": "token_verified"
            }
        else:
            return {
                "authenticated": False,
                "message": "Token exists but not working. Please re-authenticate.",
                "debug": f"token_invalid: {response.get('message', 'unknown')}"
            }
    except Exception as e:
        print(f"[AUTH STATUS] Token validation failed: {str(e)}")
        return {
            "authenticated": False,
            "message": "Token validation failed. Please re-authenticate.",
            "debug": f"validation_error: {str(e)}"
        }



@router.get("/refresh")
def refresh_tokens():
    """
    Force-refresh the access token using the stored refresh token.
    """
    tokens_collection = database.tokens_collection
    if tokens_collection is None:
        raise HTTPException(status_code=500, detail="Tokens storage not available")

    token_doc = tokens_collection.find_one()
    if not token_doc or "refresh_token" not in token_doc:
        raise HTTPException(status_code=400, detail="No refresh token available. Re-authenticate.")

    try:
        new_tokens = fyers_service.refresh_access_token()
        return {"message": "Tokens refreshed", "detail": new_tokens}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {e}")
