import { useState, useRef, useCallback } from "react";
import { ENDPOINTS } from "../utils/api/endpoints.js";
import { SimulationForm } from "../components/SimulationForm.jsx";
import { SimulationStats } from "../components/SimulationStats.jsx";
import { SimulationControls } from "../components/SimulationControls.jsx";

const DEFAULT_CONFIG = {
  population_size: 200,
  grid_size: 100.0,
  initial_infected: 5,
  infection_rate: 1.5,
  incubation_mean: 5.0,
  incubation_std: 2.0,
  infectious_mean: 10.0,
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
  const [isRunning, setIsRunning] = useState(false);
  const canvasRef = useRef();
  const runningRef = useRef(false);

  function handleChange(e) {
    const { name, value } = e.target;
    setConfig((prev) => ({
      ...prev,
      [name]: isNaN(Number(value)) ? value : Number(value),
    }));
  }

  async function createSimulation() {
    const res = await fetch(ENDPOINTS.SIMULATIONS, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    const data = await res.json();
    setSimulationId(data.simulation_id);
    return data.simulation_id;
  }

  const drawAgents = useCallback(async (simId) => {
    const id = simId || simulationId;
    if (!id) return;
    const res = await fetch(`${ENDPOINTS.SIMULATIONS}/${id}/agents`);
    const data = await res.json();
    const { agents, state_colors, grid_size } = data;

    const canvas = canvasRef.current;
    if (!canvas) return;
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
  }, [simulationId]);

  const fetchStats = useCallback(async (id) => {
    const res = await fetch(`${ENDPOINTS.SIMULATIONS}/${id}/stats`);
    const data = await res.json();
    setStats(data);
  }, []);

  // Continuous simulation loop
  const runLoop = useCallback(async (simId) => {
    if (!runningRef.current) return;

    try {
      const stepResponse = await fetch(`${ENDPOINTS.SIMULATIONS}/${simId}/step`, {
        method: "POST",
      });

      if (!stepResponse.ok) {
        if (stepResponse.status === 400) {
          // Simulation completed
          console.log("Simulation completed");
          runningRef.current = false;
          setIsRunning(false);
          return;
        }
        throw new Error(`Step failed with status ${stepResponse.status}`);
      }

      await fetchStats(simId);
      await drawAgents(simId);

      // Continue loop if still running
      if (runningRef.current) {
        setTimeout(() => runLoop(simId), 50);
      }
    } catch (error) {
      console.error("Simulation error:", error);
      runningRef.current = false;
      setIsRunning(false);
    }
  }, [fetchStats, drawAgents]);

  async function handleStart() {
    let simId = simulationId;
    
    // Create simulation if not exists
    if (!simId) {
      simId = await createSimulation();
      await fetchStats(simId);
      await drawAgents(simId);
    }

    // Start continuous loop
    runningRef.current = true;
    setIsRunning(true);
    runLoop(simId);
  }

  function handleStop() {
    runningRef.current = false;
    setIsRunning(false);
  }

  async function handleReset() {
    runningRef.current = false;
    setIsRunning(false);
    setStats(null);
    
    // Create new simulation
    const simId = await createSimulation();
    await fetchStats(simId);
    await drawAgents(simId);
  }

  return (
    <div className="p-4 pb-4">
      <h1 className="text-3xl font-bold mb-2">PANDEMIC SIMULATION</h1>
      <p className="mb-6 text-gray-700">
        Configure the simulation parameters below, then use the controls to
        run the simulation. Press <strong>Start</strong> to begin continuous
        simulation, <strong>Stop</strong> to pause, and <strong>Reset</strong> to
        restart with current parameters.
      </p>
      <div className="flex item-center gap-8 px-4 justify-center">
        <div>
          <h1 className="font-bold text-xl">CONFIGURATION</h1>
          <SimulationForm config={config} onChange={handleChange} />
          <SimulationControls
            simulationId={simulationId}
            isRunning={isRunning}
            onStart={handleStart}
            onStop={handleStop}
            onReset={handleReset}
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
