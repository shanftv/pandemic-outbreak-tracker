export function SimulationForm({ config, onChange }) {
  return (
    <form className="grid grid-cols-2 gap-4 mb-4">
      {Object.entries(config).map(([key, value]) => (
        <div key={key}>
          <label className="block text-xs font-semibold mb-1">
            {key.replace(/_/g, " ")}
          </label>
          <input
            type="number"
            name={key}
            value={value}
            onChange={onChange}
            className="w-full border rounded px-2 py-1"
            step="any"
          />
        </div>
      ))}
    </form>
  );
}
