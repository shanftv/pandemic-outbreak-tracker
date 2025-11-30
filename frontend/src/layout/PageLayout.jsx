import { NavBar } from "../components/NavBar.jsx";

export function PageLayout({ children }) {
  return (
    <>
      <div className="min-h-screen bg-(--background-color)">
        <NavBar />
        {children}
      </div>
    </>
  );
}
