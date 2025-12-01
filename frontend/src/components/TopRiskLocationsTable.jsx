import { useEffect, useState } from "react";
import { ENDPOINTS } from "../utils/api/endpoints.js";

export function TopRiskLocationsTable() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch(ENDPOINTS.PREDICTIONS_SUMMARY)
      .then((res) => res.json())
      .then((data) => setStats(data));
  }, []);

  if (!stats) return <div className="text-center py-8">Loading...</div>;
  return (
    <div className="p-4">
      <div>
        <h2 className="text-xl font-semibold mb-2 ">TOP 5 RISK LOCATIONS</h2>
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
