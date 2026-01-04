import { MdAccountBalance } from "react-icons/md";
import "./Navigation.css";

export default function Navigation() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <MdAccountBalance className="brand-icon" size={28} />
        <span className="brand-text">Fyers Trading</span>
      </div>
      <div className="navbar-actions">
        {/* Future: Add user profile, notifications, etc */}
      </div>
    </nav>
  );
}
