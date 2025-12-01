const LEGENDS = {
  current: [
    { label: "Low Risk (0-25)", color: "#4CAF50" },
    { label: "Moderate Risk (25-50)", color: "#FFC107" },
    { label: "High Risk (50-75)", color: "#FF9800" },
    { label: "Critical Risk (75-100)", color: "#F44336" },
  ],
  prediction: [
    { label: "Low Predicted (0-25)", color: "#81C784" },
    { label: "Moderate Predicted (25-50)", color: "#FFD54F" },
    { label: "High Predicted (50-75)", color: "#FFB74D" },
    { label: "Critical Predicted (75-100)", color: "#E57373" },
  ],
};

export function IntensityLegendModal({ mode = "current" }) {
  const legend = LEGENDS[mode];
  const gradient = `linear-gradient(to right, ${legend
    .map((l) => l.color)
    .join(", ")})`;

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 w-full max-w-sm">
      <h1 className="text-xl font-bold mb-2">INTENSITY LEGEND</h1>
      <p className="mb-1 font-regular">
        {mode === "current" ? "Current Outbreak" : "7-Day Prediction"}
      </p>
      <div
        className="w-full h-4 rounded mb-4 border-gray-400 border "
        style={{ background: gradient }}
      ></div>
      <ul className="space-y-3 mb-2">
        {legend.map((item) => (
          <li key={item.label} className="flex items-center gap-3">
            <span
              className="inline-block w-4 h-4 rounded-full border border-gray-400"
              style={{ backgroundColor: item.color }}
              title={item.label}
            ></span>
            <span className="text-gray-700">{item.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
