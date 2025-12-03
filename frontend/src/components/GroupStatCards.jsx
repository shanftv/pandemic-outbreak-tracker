import { useEffect, useState } from "react";
import { StatCard } from "./StatCard.jsx";
import { ENDPOINTS } from "../utils/api/endpoints.js";

export function GroupStatCards() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch(ENDPOINTS.PREDICTIONS_SUMMARY)
      .then((res) => res.json())
      .then((data) => setStats(data));
  }, []);

  if (!stats) return <div className="text-center py-8">Loading...</div>;

  const statCards = [
    {
      title: "TOTAL LOCATIONS",
      value: stats.total_locations,
      color: "bg-[#195E63]",
      icon: <i className="bx bxs-city "></i>,
    },
    {
      title: "TOTAL PREDICTED CASES",
      value: stats.total_predicted_cases,
      color: "bg-[#DF8E4D]",
      icon: <i className="bx bxs-virus "></i>,
    },
    {
      title: "INCREASING LOCATIONS",
      value: stats.increasing_locations,
      color: "bg-[#943C30]",
      icon: <i className='bx  bxs-trending-up'></i> 
    },
    {
      title: "DECREASING LOCATIONS",
      value: stats.decreasing_locations,
      color: "bg-[#5C946D]",
      icon: <i className="bx bxs-trending-down"></i>,
    },
    {
      title: "STABLE LOCATIONS",
      value: stats.stable_locations,
      color: "bg-[#3F4E61]",
      icon: <i className="bx bxs-minus-circle "></i>,
    },
  ];

  return (
    <div className="space-y-6 p-4">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 p-4 bg-white rounded-lg shadow-lg">
        {statCards.map((card) => (
          <StatCard
            key={card.title}
            title={card.title}
            value={card.value}
            color={card.color}
            icon={card.icon}
          />
        ))}
      </div>

     
    </div>
  );
}
