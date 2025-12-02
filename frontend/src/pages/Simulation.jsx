import { useState, useRef, useEffect } from "react";
import { ENDPOINTS } from "../utils/api/endpoints.js";
import { SimulationForm } from "../components/SimulationForm.jsx";
import { SimulationStats } from "../components/SimulationStats.jsx";
import { SimulationControls } from "../components/SimulationControls.jsx";

const DEFAULT_CONFIG = {
  population_size: 200,
  grid_size: 100.0,
  initial_infected: 1,
  infection_rate: 1.0,
  incubation_mean: 5.0,
  incubation_std: 2.0,
  infectious_mean: 7.0,
  infectious_std: 3.0,
  mortality_rate: 0.02,
  vaccination_rate: 0.0,
  detection_probability: 0.0,
  isolation_compliance: 0.8,
  home_attraction: 0.05,
  random_movement: 1.0,
  time_step: 0.5,
};

export function Simulation() {
  document.title = "Simulation | Pandemic Outbreak Tracker";
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [simulationId, setSimulationId] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const canvasRef = useRef();

  function handleChange(e) {
    const { name, value } = e.target;
    setConfig((prev) => ({
      ...prev,
      [name]: isNaN(Number(value)) ? value : Number(value),
    }));
  }

  async function createSimulation() {
    setLoading(true);
    const res = await fetch(ENDPOINTS.SIMULATIONS, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    const data = await res.json();
    setSimulationId(data.simulation_id);
    setLoading(false);
    fetchStats(data.simulation_id);
    await drawAgents();
  }

  async function drawAgents() {
    if (!simulationId) return;
    const res = await fetch(`${ENDPOINTS.SIMULATIONS}/${simulationId}/agents`);
    const data = await res.json();
    const { agents, state_colors, grid_size } = data;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    agents.forEach((agent) => {
      ctx.fillStyle = state_colors[agent.state];
      ctx.beginPath();
      ctx.arc(
        (agent.x / grid_size) * canvas.width,
        (agent.y / grid_size) * canvas.height,
        5,
        0,
        Math.PI * 2
      );
      ctx.fill();
    });
  }

  async function stepSimulation() {
    if (!simulationId) return;
    setLoading(true);
    await fetch(`${ENDPOINTS.SIMULATIONS}/${simulationId}/step`, {
      method: "POST",
    });
    fetchStats(simulationId);
    await drawAgents();
    setLoading(false);
  }

  async function runSimulation() {
    if (!simulationId) return;
    setLoading(true);
    await fetch(`${ENDPOINTS.SIMULATIONS}/${simulationId}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ steps: 100 }),
    });
    fetchStats(simulationId);
    await drawAgents();
    setLoading(false);
  }

  async function fetchStats(id) {
    const res = await fetch(`${ENDPOINTS.SIMULATIONS}/${id}/stats`);
    const data = await res.json();
    setStats(data);
  }

  return (
    <div className="p-4 pb-4">
      <h1 className="text-3xl font-bold mb-2">PANDEMIC SIMULATION</h1>
      <p className="mb-6 text-gray-700">
        Configure the simulation parameters below, then start and step/run the
        simulation to visualize the spread of disease among agents. Use the
        "Step" button to advance one time step, or "Run 100 Steps" for a longer
        simulation. The agent scatter chart shows each individual's state and
        position.
      </p>
      <div className="flex item-center gap-8 px-4 justify-center">
        <div>
          <h1 className="font-bold text-xl">CONFIGURATION</h1>
          <SimulationForm config={config} onChange={handleChange} />
          <SimulationControls
            simulationId={simulationId}
            loading={loading}
            createSimulation={createSimulation}
            stepSimulation={stepSimulation}
            runSimulation={runSimulation}
            drawAgents={drawAgents}
          />
        </div>

        <div>
          {simulationId && (
            <div className="transition-all duration-500 ease-in-out opacity-100 animate-fade-in">
              <h2 className="text-lg font-bold my-2">AGENT VISUALIZATION</h2>
              <div className="flex gap-4 justify-center">
                <div>
                  <canvas
                    ref={canvasRef}
                    width={600}
                    height={600}
                    className="bg-(--color-white) p-4 shadow-lg rounded-lg"
                  ></canvas>
                </div>
                <div>
                  {stats && (
                    <div className="">
                      <SimulationStats stats={stats} />
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
