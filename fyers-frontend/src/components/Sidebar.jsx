import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { 
  MdDashboard, 
  MdTrendingUp, 
  MdHistory, 
  MdLightbulb,
  MdShowChart,
  MdInsights,
  MdMenu,
  MdChevronLeft
} from "react-icons/md";
import "./Sidebar.css";

const menuItems = [
  { path: "/", icon: MdDashboard, label: "Dashboard" },
  { path: "/automated-trading", icon: MdTrendingUp, label: "Automated Trading" },
  { path: "/trading-history", icon: MdHistory, label: "Trading History" },
  { path: "/strategies", icon: MdLightbulb, label: "Strategies" },
  { path: "/historical", icon: MdShowChart, label: "Historical Data" },
  { path: "/indicators", icon: MdInsights, label: "Indicators" },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  // Update CSS variable when sidebar state changes
  const handleToggle = () => {
    const newState = !collapsed;
    setCollapsed(newState);
    document.documentElement.style.setProperty(
      '--current-sidebar-width',
      newState ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)'
    );
  };

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-header">
        <button 
          className="sidebar-toggle"
          onClick={handleToggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <MdMenu size={20} /> : <MdChevronLeft size={20} />}
        </button>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`sidebar-item ${isActive ? "active" : ""}`}
              title={collapsed ? item.label : ""}
            >
              <Icon className="sidebar-icon" size={20} />
              <span className="sidebar-label">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
