const labels = { low: "Low", medium: "Medium", high: "High" };

export default function RiskBadge({ level }) {
  return <span className={`badge ${level}`}><i className="dot" />{labels[level] ?? level}</span>;
}
