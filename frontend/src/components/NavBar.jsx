export function NavBar() {
  return (
    <nav className="bg-(--color-gray) p-5 flex justify-between items-center">
      <h1 className="text-xl text-(--color-white) font-medium">
        COVID-19 Philippines Disease Outbreak Dashboard
      </h1>
      <ul className="flex gap-4 text-lg font-light text-(--color-white) cursor-pointer">
        <li>Dashboard</li>
        <li>Simulation</li>
        <li>About</li>
      </ul>
    </nav>
  );
}
