import { useState, useEffect } from "react";
import { MdWarning } from "react-icons/md";
import { getLoginUrl, checkHealth } from "../api/fyersApi";
import "./AuthButton.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function AuthButton() {
  const [isAuthenticated, setIsAuthenticated] = useState(null); // null = checking, true/false = status
  const [isChecking, setIsChecking] = useState(true);
  const [healthStatus, setHealthStatus] = useState(null);
  const [hasShownPopup, setHasShownPopup] = useState(false);

  useEffect(() => {
    checkBackendHealth();
    checkAuthStatus();
    
    // Check if we just returned from a login attempt
    const loginInProgress = sessionStorage.getItem('fyers_login_in_progress');
    const loginTimestamp = sessionStorage.getItem('fyers_login_timestamp');
    
    if (loginInProgress) {
      const elapsed = Date.now() - parseInt(loginTimestamp || '0');
      console.log(`⏱️ Returned from Fyers login after ${elapsed}ms`);
      console.log(`📍 Current URL: ${window.location.href}`);
      console.log(`🔍 Checking authentication status...`);
      
      // Clean up
      sessionStorage.removeItem('fyers_login_in_progress');
      sessionStorage.removeItem('fyers_login_timestamp');
    }
    
    // Check auth status every 30 seconds (but don't show popup repeatedly)
    const interval = setInterval(() => {
      checkAuthStatus(true); // Pass true to indicate it's a background check
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkBackendHealth = async () => {
    const health = await checkHealth();
    setHealthStatus(health);
    setIsChecking(false);
  };

  const checkAuthStatus = async (isBackgroundCheck = false) => {
    try {
      const response = await fetch(`${API_BASE}/auth/status`);
      const data = await response.json();
      const authenticated = data.authenticated || false;
      
      // Only update state if it actually changed or if it's the first check
      if (isAuthenticated !== authenticated) {
        setIsAuthenticated(authenticated);
      }
      
      // Mark that we've shown the popup on first load if not authenticated
      if (!isBackgroundCheck && !authenticated && !hasShownPopup) {
        setHasShownPopup(true);
      }
    } catch (error) {
      console.error("Failed to check auth status:", error);
      // Don't change auth state on network errors
    }
  };

  const handleReAuthenticate = async () => {
    try {
      console.log("Fetching login URL...");
      const { login_url } = await getLoginUrl();
      console.log("Redirecting to Fyers login URL:", login_url);
      
      if (!login_url || login_url.includes("undefined")) {
        alert("Invalid login URL generated. Please check backend configuration.");
        return;
      }
      
      // Store a flag to indicate login in progress
      sessionStorage.setItem('fyers_login_in_progress', 'true');
      sessionStorage.setItem('fyers_login_timestamp', Date.now().toString());
      
      console.log("🔐 Redirecting to Fyers login...");
      console.log("📍 Make sure to complete the login on Fyers page");
      console.log("🔄 You will be redirected back after authentication");
      
      // Direct redirect - don't use window.open or loading overlay
      // This ensures the OAuth flow works properly
      window.location.href = login_url;
    } catch (error) {
      console.error("Re-authentication error:", error);
      alert(`Failed to initiate authentication: ${error.message}\n\nPlease ensure:\n1. Backend is running on port 8000\n2. Redirect URI is registered in Fyers dashboard`);
      sessionStorage.removeItem('fyers_login_in_progress');
    }
  };

  // Don't show anything while checking
  if (isChecking || isAuthenticated === null) {
    return null;
  }

  if (healthStatus?.status !== "ok") {
    return (
      <div style={{ 
        padding: "15px", 
        backgroundColor: "#fee", 
        border: "1px solid #fcc",
        borderRadius: "8px",
        margin: "10px 0"
      }}>
        <strong>⚠️ Backend Connection Issue</strong>
        <p style={{ margin: "5px 0", fontSize: "0.9em" }}>
          Unable to connect to backend server. Please ensure the backend is running.
        </p>
      </div>
    );
  }

  // Only show the popup if user is NOT authenticated AND we haven't shown it yet this session
  if (isAuthenticated || !hasShownPopup) {
    return null;
  }

  return (
    <div className="auth-button-container">
      <div className="auth-status">
        <div className="auth-info">
          <MdWarning className="auth-icon warning" size={28} />
          <div>
            <strong className="auth-title">Authentication Required</strong>
            <p className="auth-message">Please authenticate with Fyers to access market data</p>
          </div>
        </div>
        <button
          onClick={handleReAuthenticate}
          className="auth-button"
        >
          Re-authenticate
        </button>
      </div>
    </div>
  );
}

