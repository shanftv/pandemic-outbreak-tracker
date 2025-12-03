export function StatCard({ title, value, color, icon }) {
  return (
    <div
      className={`rounded-lg shadow p-4 text-(--color-white) ${color} shadow-lg flex items-center gap-4`}
    >
      <span className="text-3xl">{icon}</span>
      <div>
        <h1 className="text-2xl font-bold">{value}</h1>
        <p className="text-sm">{title}</p>
      </div>
    </div>
  );
}
