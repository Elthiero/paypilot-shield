import { Navigate, Route, Routes } from "react-router-dom";
import Shell from "./components/Shell";
import { isLoggedIn } from "./hooks/useAuth";
import AgentChat from "./pages/AgentChat";
import Approvals from "./pages/Approvals";
import Invoices from "./pages/Invoices";
import Login from "./pages/Login";
import Payments from "./pages/Payments";
import Policy from "./pages/Policy";
import Replay from "./pages/Replay";
import Suppliers from "./pages/Suppliers";

function Guard() {
  return isLoggedIn() ? <Shell /> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
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
