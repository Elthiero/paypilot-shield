import { Link } from "react-router-dom";

// Leave empty to hide the contact line.
const CONTACT = "thierrydonambi@gmail.com";

export default function Privacy() {
  return (
    <div className="min-h-screen flex justify-center p-6">
      <article className="card max-w-2xl w-full space-y-4 self-start">
        <Link to="/" className="label underline">Back</Link>
        <h1>Privacy and terms</h1>
        <p><b>PayPilot Shield is a sandbox demo.</b> It uses the PayPal sandbox, so no real money moves. Please do not enter real personal, banking or customer data.</p>

        <h2>What is stored</h2>
        <ul className="list-disc pl-5 space-y-1">
          <li>The owner account: email and a password hash (never the password).</li>
          <li>Your public signing key. The private key is created in your browser, cannot be exported, and never reaches the server.</li>
          <li>Suppliers, invoices (including payee emails and description text), payment requests, approvals, signed policies and the audit log.</li>
          <li>Failed login attempts, with the visitor IP address and email, to limit guessing.</li>
        </ul>

        <h2>Who else sees data</h2>
        <ul className="list-disc pl-5 space-y-1">
          <li><b>AI provider.</b> When AI mode is on, your chat messages and the invoice details the agent looks up (number, supplier, amount, status, description) are sent to the AI provider, Groq. The rules engine, not the AI, decides payments.</li>
          <li><b>PayPal sandbox.</b> Payout requests send the payee email and amount to PayPal.</li>
          <li><b>Google Fonts.</b> Your browser loads fonts from Google, which sees your IP address.</li>
        </ul>

        <h2>In your browser</h2>
        <p>Your login is an httpOnly, same-site session cookie that page scripts cannot read, and your email is kept in session storage until you sign out or close the tab. It is a login cookie only, not a tracking cookie. The signing key is kept in IndexedDB. There are no analytics or advertising trackers.</p>

        <h2>Terms</h2>
        <p>Provided as is, for demonstration only, with no warranty. Demo data may be reset or deleted at any time.</p>

        {CONTACT && <p>Contact: {CONTACT}</p>}
      </article>
    </div>
  );
}
