import { useState } from "react";
import { NavBar } from "../components/NavBar.jsx";
import { AboutModal } from "../pages/About.jsx";

export function PageLayout({ children }) {
  const [aboutOpen, setAboutOpen] = useState(false);

  return (
    <>
      <div className="min-h-screen bg-(--background-color)">
        <NavBar />

        {children}

        <button
          onClick={() => setAboutOpen(true)}
          className="fixed bottom-6 right-6 w-16 h-16 bg-[var(--color-gray)] text-white rounded-full shadow-lg hover:bg-gray-700 focus:outline-none focus:ring-4 focus:ring-gray-500 focus:ring-opacity-50 transition-all duration-200 flex items-center justify-center hover:scale-105 z-[9999]"
        >
          <i className="bx bx-info-circle text-2xl"></i>
        </button>

        <AboutModal isOpen={aboutOpen} setIsOpen={setAboutOpen} />
      </div>
    </>
  );
}
