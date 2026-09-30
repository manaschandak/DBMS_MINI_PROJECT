import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import BatteryDetail from "./pages/BatteryDetail";
import Alerts from "./pages/Alerts";

export default function App() {
  return (
    <BrowserRouter>
      <header className="topbar">
        <div className="wrap bar">
          <span className="brand">Battery thermal monitor</span>
          <nav>
            <NavLink to="/" end>Fleet</NavLink>
            <NavLink to="/alerts">Alerts</NavLink>
          </nav>
        </div>
      </header>
      <main className="wrap">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/battery/:id" element={<BatteryDetail />} />
          <Route path="/alerts" element={<Alerts />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}