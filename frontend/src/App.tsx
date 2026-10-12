import { useEffect } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import Shell from "./components/Shell";
import { isLoggedIn } from "./hooks/useAuth";
import AgentChat from "./pages/AgentChat";
import Approvals from "./pages/Approvals";
import Invoices from "./pages/Invoices";
import Login from "./pages/Login";
import Payments from "./pages/Payments";
import Policy from "./pages/Policy";
import Privacy from "./pages/Privacy";
import Replay from "./pages/Replay";
import Suppliers from "./pages/Suppliers";

function Guard() {
  return isLoggedIn() ? <Shell /> : <Navigate to="/login" replace />;
}

const TITLES: Record<string, string> = {
  "/login": "Sign in", "/privacy": "Privacy and terms", "/": "Agent", "/policy": "Policy", "/approvals": "Approvals",
  "/payments": "Payments", "/invoices": "Invoices", "/suppliers": "Suppliers",
};

export default function App() {
  const { pathname } = useLocation();
  useEffect(() => {
    document.title = `${TITLES[pathname] ?? (pathname.startsWith("/replay") ? "Replay" : "PayPilot")} | PayPilot Shield`;
  }, [pathname]);
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route element={<Guard />}>
        <Route path="/" element={<AgentChat />} />
        <Route path="/policy" element={<Policy />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/payments" element={<Payments />} />
        <Route path="/invoices" element={<Invoices />} />
        <Route path="/suppliers" element={<Suppliers />} />
        <Route path="/replay/:id" element={<Replay />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
