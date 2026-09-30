const colors = { low: "#2e7d32", medium: "#ed6c02", high: "#d32f2f" };

export default function RiskBadge({ level }) {
  return (
    <span style={{ background: colors[level], color: "#fff", padding: "2px 10px", borderRadius: 12, fontSize: 12 }}>
      {level}
    </span>
  );
}