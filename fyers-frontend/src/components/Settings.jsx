import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { MdSettings, MdLogout, MdLogin, MdPerson } from "react-icons/md";
import { getAuthStatus, logout, getLoginUrl } from "../api/fyersApi";
import "./Settings.css";

export default function Settings() {
  const [authStatus, setAuthStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loggingOut, setLoggingOut] = useState(false);
  const [message, setMessage] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const status = await getAuthStatus();
      setAuthStatus(status);
    } catch (error) {
      console.error("Failed to check auth status:", error);
      setAuthStatus({ authenticated: false, message: "Error checking status" });
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    if (!window.confirm("Are you sure you want to logout? You will need to re-authenticate to access trading features.")) {
      return;
    }

    setLoggingOut(true);
    setMessage(null);

    try {
      const result = await logout();
      setMessage({ type: "success", text: "Logged out successfully! You can now login with a different account." });
      
      // Update auth status
      await checkAuthStatus();
      
      // Redirect to home page after a short delay
      setTimeout(() => {
        navigate("/");
      }, 2000);
    } catch (error) {
      console.error("Logout failed:", error);
      setMessage({ type: "error", text: `Logout failed: ${error.message}` });
    } finally {
      setLoggingOut(false);
    }
  };

  const handleLogin = async () => {
    try {
      const response = await getLoginUrl();
      if (response.login_url) {
        // Open login URL in same tab
        window.location.href = response.login_url;
      }
    } catch (error) {
      console.error("Failed to get login URL:", error);
      setMessage({ type: "error", text: `Failed to initiate login: ${error.message}` });
    }
  };

  if (loading) {
    return (
      <div className="settings-container">
        <div className="settings-loading">
          <p>Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="settings-container">
      <div className="settings-header">
        <h1>Settings</h1>
        <p>Manage your account and application preferences</p>
      </div>

      {message && (
        <div className={message.type === "success" ? "logout-success-msg" : "logout-error-msg"}>
          {message.text}
        </div>
      )}

      <div className="settings-section">
        <h2>
          <MdPerson size={24} />
          Account
        </h2>

        <div className={`auth-status ${authStatus?.authenticated ? "authenticated" : "unauthenticated"}`}>
          <span className="auth-status-dot"></span>
          <span className="auth-status-text">
            {authStatus?.authenticated ? "Connected to Fyers" : "Not Connected"}
          </span>
        </div>

        <div className="settings-item">
          <div className="settings-item-info">
            <h3>Fyers Authentication</h3>
            <p>
              {authStatus?.authenticated
                ? "You are currently logged in. Click logout to disconnect and login with a different account."
                : "You are not logged in. Click login to authenticate with your Fyers account."}
            </p>
          </div>

          {authStatus?.authenticated ? (
            <button
              className="logout-btn"
              onClick={handleLogout}
              disabled={loggingOut}
            >
              <MdLogout size={18} />
              {loggingOut ? "Logging out..." : "Logout"}
            </button>
          ) : (
            <button className="login-btn" onClick={handleLogin}>
              <MdLogin size={18} />
              Login
            </button>
          )}
        </div>
      </div>

      <div className="settings-section">
        <h2>
          <MdSettings size={24} />
          About
        </h2>
        <div className="settings-item">
          <div className="settings-item-info">
            <h3>Version</h3>
            <p>Fyers OHLC Trading Dashboard v1.0.0</p>
          </div>
        </div>
        <div className="settings-item">
          <div className="settings-item-info">
            <h3>Description</h3>
            <p>
              Advanced trading platform with automated strategies, technical
              indicators, and real-time market data integration.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
