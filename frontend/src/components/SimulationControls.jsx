export function SimulationControls({
  simulationId,
  loading,
  createSimulation,
  stepSimulation,
  runSimulation,
  drawAgents,
}) {
  return (
    <div className="flex flex-wrap gap-2 mt-4">
      <button
        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition cursor-pointer"
        onClick={createSimulation}
        disabled={loading}
      >
        Start Simulation
      </button>
      <button
        className={`${
          !simulationId
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-green-600 hover:bg-green-700"
        } text-white px-4 py-2 rounded-lg transition`}
        onClick={stepSimulation}
        disabled={!simulationId || loading}
      >
        Step
      </button>
      <button
        className={`${
          !simulationId
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-purple-600 hover:bg-purple-700"
        } text-white px-4 py-2 rounded-lg transition`}
        onClick={runSimulation}
        disabled={!simulationId || loading}
      >
        Run 100 Steps
      </button>
      <button
        className={`${
          !simulationId
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-gray-600 hover:bg-gray-700"
        } text-white px-4 py-2 rounded-lg transition`}
        onClick={drawAgents}
        disabled={!simulationId}
      >
        Draw Agents
      </button>
      <button
        className={`${
          !simulationId
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-orange-600 hover:bg-orange-700"
        } text-white px-4 py-2 rounded-lg transition`}
        onClick={createSimulation}
        disabled={!simulationId || loading}
      >
        Restart Simulation
      </button>
    </div>
  );
}
