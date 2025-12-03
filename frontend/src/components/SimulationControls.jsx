export function SimulationControls({
  simulationId,
  isRunning,
  onStart,
  onStop,
  onReset,
}) {
  return (
    <div className="flex gap-2 mt-4">
      <button
        className={`${
          isRunning
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-emerald-600 hover:bg-emerald-700"
        } text-white px-5 py-2.5 rounded-lg transition font-medium`}
        onClick={onStart}
        disabled={isRunning}
      >
        Start
      </button>
      <button
        className={`${
          !isRunning
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-amber-600 hover:bg-amber-700"
        } text-white px-5 py-2.5 rounded-lg transition font-medium`}
        onClick={onStop}
        disabled={!isRunning}
      >
        Stop
      </button>
      <button
        className="bg-slate-600 hover:bg-slate-700 text-white px-5 py-2.5 rounded-lg transition font-medium"
        onClick={onReset}
      >
        Reset
      </button>
    </div>
  );
}
