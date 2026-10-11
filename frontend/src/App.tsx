import { Link, Route, Routes } from "react-router-dom";
import Login from "./pages/Login";
import AgentChat from "./pages/AgentChat";
import Approvals from "./pages/Approvals";
import Invoices from "./pages/Invoices";
import Suppliers from "./pages/Suppliers";
import Payments from "./pages/Payments";
import Replay from "./pages/Replay";
import Policy from "./pages/Policy";

export default function App() {
  return (
    <div style={{ fontFamily: "system-ui", padding: 16 }}>
      <nav style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <Link to="/">Agent</Link>
        <Link to="/policy">Policy</Link>
        <Link to="/approvals">Approvals</Link>
        <Link to="/payments">Payments</Link>
        <Link to="/invoices">Invoices</Link>
        <Link to="/suppliers">Suppliers</Link>
      </nav>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<AgentChat />} />
        <Route path="/policy" element={<Policy />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/payments" element={<Payments />} />
        <Route path="/invoices" element={<Invoices />} />
        <Route path="/suppliers" element={<Suppliers />} />
        <Route path="/replay/:id" element={<Replay />} />
      </Routes>
    </div>
  );
}
