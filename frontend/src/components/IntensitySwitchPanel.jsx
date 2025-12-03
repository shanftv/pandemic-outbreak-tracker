export function IntensitySwitchPanel({ mode, setMode }) {
  const options = [
    { value: "current", label: "Current Outbreak" },
    { value: "prediction", label: "7-Day Prediction" },
  ];

  return (
    <div className="bg-white rounded-lg shadow-lg p-4 flex flex-col gap-2">
      <h2 className="text-sm font-semibold">MAP LAYERS</h2>
      {options.map((opt) => (
        <label key={opt.value} className="flex items-center cursor-pointer">
          <input
            type="radio"
            name="intensity-mode"
            value={opt.value}
            checked={mode === opt.value}
            onChange={() => setMode(opt.value)}
            className="form-radio accent-gray-600 mr-2"
          />
          <span className="text-xs">{opt.label}</span>
        </label>
      ))}
    </div>
  );
}