import { useEffect, useState } from "react";
import { StatCard } from "./StatCard.jsx";

export function GroupStatCards() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/predictions/summary")
      .then((res) => res.json())
      .then((data) => setStats(data));
  }, []);

  if (!stats) return <div className="text-center py-8">Loading...</div>;

  const statCards = [
    {
      title: "TOTAL LOCATIONS",
      value: stats.total_locations,
      color: "bg-[#195E63]",
      icon: ""
    },
    {
      title: "TOTAL PREDICTED CASES",
      value: stats.total_predicted_cases,
      color: "bg-[#DF8E4D]",
      icon: ""
    },
    {
      title: "INCREASING LOCATIONS",
      value: stats.increasing_locations,
      color: "bg-[#943C30]",
      icon: ""
    },
    {
      title: "DECREASING LOCATIONS",
      value: stats.decreasing_locations,
      color: "bg-[#5C946D]",
      icon: ""
    },
    {
      title: "STABLE LOCATIONS",
      value: stats.stable_locations,
      color: "bg-[#3F4E61]",
      icon: ""
    },
  ];

  return (
    <div className="space-y-6 p-4">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 p-4 bg-(--color-white) rounded-lg shadow-lg">
        {statCards.map((card) => (
          <StatCard
            key={card.title}
            title={card.title}
            value={card.value}
            color={card.color}
          />
        ))}
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-2">Top 5 Risk Locations</h2>
        <div className="rounded-lg  p-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="py-2 text-left">Location</th>
                <th className="py-2 text-left">Predicted Cases</th>
                <th className="py-2 text-left">Trend</th>
              </tr>
            </thead>
            <tbody>
              {stats.top_5_risk.map((loc) => (
                <tr key={loc.location} className="border-b last:border-none">
                  <td className="py-2">{loc.location}</td>
                  <td className="py-2">{loc.predicted_cases}</td>
                  <td className="py-2 capitalize">{loc.trend}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
