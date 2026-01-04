import { MdLightbulb } from "react-icons/md";
import StrategyExecutor from "./StrategyExecutor";
import MarketStatus from "./MarketStatus";
import "./StrategiesPage.css";

export default function StrategiesPage() {
  return (
    <div className="strategies-page">
      <div className="page-header">
        <h1>
          <MdLightbulb size={32} />
          Algorithmic Trading Strategies
        </h1>
        <p className="subtitle">Execute technical analysis strategies on live market data</p>
      </div>

      <MarketStatus />
      <StrategyExecutor />
    </div>
  );
}


