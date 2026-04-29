import React from "react";
import { MealPlanner } from "./components/MealPlanner";
import { SpikePrediction } from "./components/SpikePrediction";
import { RiskPrediction } from "./components/RiskPrediction";
import { ProgressTracker } from "./components/ProgressTracker";
import { GlobalExplain } from "./components/GlobalExplain";

const App: React.FC = () => {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">G</span>
          <div>
            <h1>GlucoGuide</h1>
            <p className="brand-sub">Clinical AI cockpit</p>
          </div>
        </div>
        <nav className="nav">
          <p className="nav-section-title">Modules</p>
          <ul>
            <li>1 · Meal Planner</li>
            <li>2 · Spike Prediction</li>
            <li>3 · Complication Risk</li>
            <li>4 · Progress Tracker</li>
            <li>5 · XAI Overview</li>
          </ul>
          <p className="nav-footnote">
            Ensure all FastAPI services are running
            <br />
            (run_all_modules.bat + Module 5).
          </p>
        </nav>
      </aside>
      <main className="main">
        <header className="topbar">
          <div>
            <h2>Clinical dashboard</h2>
            <p>
              End‑to‑end view of meals, spikes, complications, and symptom trends for your patients.
            </p>
          </div>
        </header>

        <div className="grid">
          <MealPlanner />
          <SpikePrediction />
          <RiskPrediction />
          <ProgressTracker />
          <GlobalExplain />
        </div>
      </main>
    </div>
  );
};

export default App;

