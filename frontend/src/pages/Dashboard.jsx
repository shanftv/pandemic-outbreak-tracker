import { NavBar } from "../components/NavBar.jsx";
import { GroupStatCards } from "../components/GroupStatCards.jsx";
import { DashboardMap } from "../components/DashboardMap.jsx";

export function Dashboard() {
  return (
    <div>
      <GroupStatCards />
      <DashboardMap></DashboardMap>
    </div>
  );
}
