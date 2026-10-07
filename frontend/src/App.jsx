import {
  HashRouter,
  Routes,
  Route,
  NavLink,
  Link,
} from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import BatteryDetail from "./pages/BatteryDetail";
import Alerts from "./pages/Alerts";

import DataEntry from "./pages/DataEntry";
import Predictions from "./pages/Predictions";
import Anomalies from "./pages/Anomalies";
import Recommendations from "./pages/Recommendations";
import Feedback from "./pages/Feedback";
import ModelPerformance from "./pages/ModelPerformance";
import Analytics from "./pages/Analytics";
import Admin from "./pages/Admin";

function Logo() {
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <rect
        x="2"
        y="7"
        width="18"
        height="11"
        rx="2.5"
        stroke="currentColor"
        strokeWidth="1.8"
      />
      <path
        d="M22 11v3"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M11.5 9.5 9 13h3l-1 3 3.5-4h-3l1-2.5z"
        fill="currentColor"
      />
    </svg>
  );
}

export default function App() {
  return (
    <HashRouter>
      <a className="skip" href="#main">
        Skip to content
      </a>

      <header className="topbar">
        <div className="wrap bar">
          <Link to="/" className="brand">
            <Logo />
            Battery thermal monitor
          </Link>

          <nav aria-label="Main">
            <NavLink to="/" end>
              Fleet
            </NavLink>

            <NavLink to="/alerts">
              Alerts
            </NavLink>

            <NavLink to="/predictions">
              Predictions
            </NavLink>

            <NavLink to="/anomalies">
              Anomalies
            </NavLink>

            <NavLink to="/analytics">
              Analytics
            </NavLink>

            <NavLink to="/recommendations">
              Recommendations
            </NavLink>

            <NavLink to="/data-entry">
              Data Entry
            </NavLink>

            <NavLink to="/feedback">
              Feedback
            </NavLink>

            <NavLink to="/model-performance">
              Models
            </NavLink>

            <NavLink to="/admin">
              Admin
            </NavLink>
          </nav>
        </div>
      </header>

      <main id="main" className="wrap">
        <Routes>
          <Route path="/" element={<Dashboard />} />

          <Route
            path="/battery/:id"
            element={<BatteryDetail />}
          />

          <Route path="/alerts" element={<Alerts />} />

          <Route
            path="/predictions"
            element={<Predictions />}
          />

          <Route
            path="/anomalies"
            element={<Anomalies />}
          />

          <Route
            path="/recommendations"
            element={<Recommendations />}
          />

          <Route
            path="/data-entry"
            element={<DataEntry />}
          />

          <Route
            path="/feedback"
            element={<Feedback />}
          />

          <Route
            path="/model-performance"
            element={<ModelPerformance />}
          />

          <Route
            path="/analytics"
            element={<Analytics />}
          />

          <Route
            path="/admin"
            element={<Admin />}
          />

          <Route
            path="*"
            element={
              <div className="state">
                <h2>Page not found</h2>
                <Link to="/">Back to fleet</Link>
              </div>
            }
          />
        </Routes>
      </main>
    </HashRouter>
  );
}