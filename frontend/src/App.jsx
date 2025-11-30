import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard.jsx";
import { PageLayout } from "./layout/PageLayout.jsx";

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
        </Routes>
      </Router>
    </>
  );
}

export default App;
