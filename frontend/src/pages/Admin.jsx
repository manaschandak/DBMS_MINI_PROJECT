import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function Admin() {
  const [allowed, setAllowed] = useState(null);

  useEffect(() => {
    api.adminCheck()
      .then(() => setAllowed(true))
      .catch(() => setAllowed(false));
  }, []);

  if (allowed === null) {
    return <div className="state">Checking admin access…</div>;
  }

  if (!allowed) {
    return (
      <div className="state">
        <h2>Access denied</h2>
        <p className="muted">
          Administrator privileges are required.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Admin</h1>
          <div className="muted">
            System and model administration.
          </div>
        </div>
      </div>

      <div className="state">
        <h2>Administration</h2>
        <p className="muted">
          Model management, system configuration and administrative
          controls will appear here.
        </p>
      </div>
    </div>
  );
}