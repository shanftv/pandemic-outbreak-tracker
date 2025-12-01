import { NavBar } from "../components/NavBar.jsx";
import { GroupStatCards } from "../components/GroupStatCards.jsx";
import { DashboardMap } from "../components/DashboardMap.jsx";
import { TopRiskLocationsTable } from "../components/TopRiskLocationsTable.jsx";

export function Dashboard() {
  return (
    <div>
      <GroupStatCards />
      <DashboardMap />
      <TopRiskLocationsTable />
    </div>
  );
}
