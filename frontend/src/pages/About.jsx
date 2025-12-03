import {
  Description,
  Dialog,
  DialogPanel,
  DialogTitle,
} from "@headlessui/react";

export function AboutModal({ isOpen, setIsOpen }) {
  return (
    <Dialog
      open={isOpen}
      onClose={() => setIsOpen(false)}
      className="relative z-[9999]"
    >
      <div className="fixed inset-0 bg-black/60" aria-hidden="true" />

      <div className="fixed inset-0 flex w-screen items-center justify-center p-4">
        <DialogPanel className="max-w-3xl space-y-6 rounded-lg bg-white p-8 shadow-xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-3xl font-bold text-gray-900">
              Pandemic Outbreak Tracker
            </DialogTitle>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-500 hover:text-gray-700 text-2xl"
              aria-label="Close dialog"
            >
              ×
            </button>
          </div>

          <Description className="text-gray-600 leading-relaxed border-l-4 border-gray-300 pl-4">
            COVID-19 Philippines infection rate prediction model using LightGBM
            regression. Generates 7-day forecasts for top provinces based on
            historical case data. Includes interactive SEIRD epidemic
            simulations for scenario modeling.
          </Description>

          <div className="space-y-6">
            <div>
              <h3 className="text-xl font-semibold text-gray-800 mb-3">
                Key Features
              </h3>
              <ul className="space-y-1 text-gray-600">
                <li>• 7-Day infection rate predictions</li>
                <li>• Color-coded danger zone visualization</li>
                <li>• REST API with FastAPI backend</li>
                <li>• Model performance metrics (MAE, RMSE, R²)</li>
                <li>• Interactive SEIRD epidemic simulations</li>
              </ul>
            </div>

            <div>
              <h3 className="text-xl font-semibold text-gray-800 mb-3">
                Technology Stack
              </h3>
              <ul className="space-y-1 text-gray-600">
                <li>
                  • <strong>Backend:</strong> Python, FastAPI
                </li>
                <li>
                  • <strong>ML Model:</strong> LightGBM Regression
                </li>
                <li>
                  • <strong>Simulations:</strong> Agent-based SEIRD model
                </li>
                <li>
                  • <strong>Frontend:</strong> React, TailwindCSS
                </li>
                <li>
                  • <strong>Maps:</strong> Mapbox/Leaflet integration
                </li>
              </ul>
            </div>

            <div>
              <h3 className="text-xl font-semibold text-gray-800 mb-3">
                Team Roles
              </h3>
              <div className="grid md:grid-cols-3 gap-4 text-gray-600">
                <div>
                  <strong>Cloud Engineer:</strong>
                  <br />
                  API development, database updates
                </div>
                <div>
                  <strong>Data Analyst:</strong>
                  <br />
                  ML model training, simulations
                </div>
                <div>
                  <strong>Web Developer:</strong>
                  <br />
                  Frontend dashboard, maps
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-xl font-semibold text-gray-800 mb-3">
                SEIRD Simulation
              </h3>
              <p className="text-gray-600 mb-2">
                Agent-based epidemic model with:
              </p>
              <ul className="space-y-1 text-gray-600 text-sm">
                <li>
                  • Disease progression: Susceptible → Exposed → Infected →
                  Recovered/Deceased
                </li>
                <li>• Spatial dynamics with movement patterns</li>
                <li>• Intervention modeling and real-time tracking</li>
              </ul>
            </div>
          </div>

          <div className="pt-4 border-t">
            <p className="text-sm text-gray-500 text-center mb-4">
              Epidemic simulation based on the SEIRD model from <a href="https://github.com/Acteus/Simple-Epidemic" target="_blank" rel="noopener noreferrer" className="underline">Simple-Epidemic</a>.
            </p>
            <div className="flex justify-end">
              <button
                onClick={() => setIsOpen(false)}
                className="px-6 py-2 bg-gray-800 text-white rounded hover:bg-gray-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </DialogPanel>
      </div>
    </Dialog>
  );
}
