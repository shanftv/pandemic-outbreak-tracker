import { Link, useLocation } from "react-router-dom";

export function NavBar() {
  const location = useLocation();

  return (
    <nav className="bg-(--color-gray) p-5 flex justify-between items-center">
      <h1 className="text-xl text-(--color-white) font-medium">
        COVID-19 Philippines Disease Outbreak Dashboard
      </h1>
      <ul className="flex gap-4 text-lg font-light text-(--color-white) cursor-pointer">
        <li
          className={`transition-colors duration-300 ${
            location.pathname === "/" ? "border-b-2" : ""
          } hover:border-b-2 hover:border-(--color-white)`}
        >
          <Link to="/">Dashboard</Link>
        </li>
        <li
          className={`transition-colors duration-300 ${
            location.pathname === "/simulation" ? "border-b-2" : ""
          } hover:border-b-2 hover:border-(--color-white)`}
        >
          <Link to="/simulation">Simulation</Link>
        </li>
     
      </ul>
    </nav>
  );
}
