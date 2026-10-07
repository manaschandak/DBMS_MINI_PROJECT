export const WARN_C = 48;
export const CRIT_C = 60;
export const TEMP_MIN = 20;
export const TEMP_MAX = 70;

export const tempStatus = (t) =>
  t >= CRIT_C ? { key: "high", label: "Critical" } : t >= WARN_C ? { key: "medium", label: "Warning" } : { key: "low", label: "Normal" };

export const healthStatus = (soh) => (soh >= 80 ? "low" : soh >= 70 ? "medium" : "high");

export const gaugePos = (t) => Math.min(100, Math.max(0, ((t - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)) * 100));

export const timeAgo = (iso) => {
  if (!iso) return "";
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const h = Math.round(mins / 60);
  return h < 24 ? `${h} h ago` : `${Math.round(h / 24)} d ago`;
};
