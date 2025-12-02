const AGENT_LEGEND = [
  { key: "susceptible", color: "#3498db", label: "Susceptible" },
  { key: "exposed", color: "#f1c40f", label: "Exposed" },
  { key: "infected", color: "#e74c3c", label: "Infected" },
  { key: "recovered", color: "#2ecc71", label: "Recovered" },
  { key: "deceased", color: "#34495e", label: "Deceased" },
];

export function SimulationStats({ stats }) {
    
  if (!stats) return null;
  return (
    <div className="bg-(--color-white) p-4 rounded-lg shadow transition-all duration-500 ease-in-out opacity-100 animate-fade-in">
      <ul>
        {AGENT_LEGEND.map((item) => (
          <li key={item.key} className="flex items-center gap-2 mb-1">
            <span
              className="inline-block w-4 h-4 rounded-full border border-gray-400"
              style={{ backgroundColor: item.color }}
            ></span>
            <span>{item.label}:</span>
            <span className="font-bold">{stats[item.key]}</span>
          </li>
        ))}
        <li className="mt-2">
          Current Rt: <span className="font-bold">{stats.current_rt}</span>
        </li>
      </ul>
    </div>
  );
}
