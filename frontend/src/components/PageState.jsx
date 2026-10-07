export function ErrorState({ error, onRetry }) {
  return (
    <div className="state" role="alert">
      <h2>Couldn't load data</h2>
      <p className="muted">{error?.message || "Something went wrong."} Check that the backend is running, or switch back to mock data.</p>
      {onRetry && <button className="btn primary" onClick={onRetry}>Try again</button>}
    </div>
  );
}

export function EmptyState({ title, hint, action }) {
  return (
    <div className="state">
      <h2>{title}</h2>
      {hint && <p className="muted">{hint}</p>}
      {action}
    </div>
  );
}

export function Skeleton({ rows = 5 }) {
  return (
    <div className="card" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }, (_, i) => <div key={i} className="skel" />)}
    </div>
  );
}
