import { BrowserRouter as Router, Routes, Route, useSearchParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import Navigation from "./components/Navigation";
import Sidebar from "./components/Sidebar";
import AuthButton from "./components/AuthButton";
import OhlcDashboard from "./components/OhlcDashboard";
import AutomatedTrading from "./components/AutomatedTrading";
import TradingHistory from "./components/TradingHistory";
import StrategiesPage from "./components/StrategiesPage";
import HistoricalData from "./components/HistoricalData";
import IndicatorsDashboard from "./components/IndicatorsDashboard";
import Settings from "./components/Settings";
import "./App.css";

function AuthCallbackHandler() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    const authStatus = searchParams.get("auth");
    const message = searchParams.get("message");

    if (authStatus) {
      if (authStatus === "success") {
        setNotification({ type: "success", text: decodeURIComponent(message || "Authentication successful!") });
        // Clear URL parameters after 3 seconds and remove notification
        setTimeout(() => {
          navigate("/", { replace: true });
          setNotification(null);
          // Force refresh auth status
          window.location.reload();
        }, 2000);
      } else if (authStatus === "error") {
        const errorMsg = decodeURIComponent(message || "Authentication failed");
        setNotification({ type: "error", text: errorMsg });
        console.error("Authentication error:", errorMsg);
        // Clear URL parameters after 5 seconds for errors
        setTimeout(() => {
          navigate("/", { replace: true });
          setNotification(null);
        }, 5000);
      }
    }
  }, [searchParams, navigate]);

  if (notification) {
    return (
      <div className="auth-notification" data-type={notification.type}>
        {notification.type === "success" ? "✓ " : "⚠ "}
        {notification.text}
      </div>
    );
  }

  return null;
}

function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        <Sidebar />
        <main className="main-content">
          <AuthButton />
          <AuthCallbackHandler />
          <Routes>
            <Route path="/" element={<OhlcDashboard />} />
            <Route path="/automated-trading" element={<AutomatedTrading />} />
            <Route path="/trading-history" element={<TradingHistory />} />
            <Route path="/strategies" element={<StrategiesPage />} />
            <Route path="/historical" element={<HistoricalData />} />
            <Route path="/indicators" element={<IndicatorsDashboard />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
