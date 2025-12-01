import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard.jsx";
import { PageLayout } from "./layout/PageLayout.jsx";
import { Simulation } from "./pages/Simulation.jsx";

function App() {
  return (
    <>
    
      <Router>
        <Routes>
          <Route
            path="/"
            element={
              <PageLayout>
                <Dashboard />
              </PageLayout>
            }
          />
           <Route
            path="/simulation"
            element={
              <PageLayout>
                <Simulation />
              </PageLayout>
            }
          />
        </Routes>
      </Router>
    </>
  );
}

export default App;
