export default function Stat({ label, value, sub, tone }) {
  const body = (
    <>
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${tone || ""}`}>{value}</div>
      {sub && <div className="stat-sub muted">{sub}</div>}
    </>
  );
  return <div className={`stat ${tone ? `stat-${tone}` : ""}`}>{body}</div>;
}
