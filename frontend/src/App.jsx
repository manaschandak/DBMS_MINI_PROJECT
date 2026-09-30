import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import BatteryDetail from "./pages/BatteryDetail";
import Alerts from "./pages/Alerts";

export default function App() {
  return (
    <BrowserRouter>
      <nav style={{ display: "flex", gap: 16, padding: 12, borderBottom: "1px solid #ddd" }}>
        <NavLink to="/">Dashboard</NavLink>
        <NavLink to="/alerts">Alerts</NavLink>
      </nav>
      <main style={{ padding: 20 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/battery/:id" element={<BatteryDetail />} />
          <Route path="/alerts" element={<Alerts />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}