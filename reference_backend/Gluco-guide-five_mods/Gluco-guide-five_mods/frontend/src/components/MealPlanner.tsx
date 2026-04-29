import React, { useState } from "react";
import { analyzeMeal, generateMealPlan } from "../api";

export const MealPlanner: React.FC = () => {
  const [form, setForm] = useState({
    patient_name: "",
    fasting_glucose: 110,
    hba1c: 7.0,
    current_glucose: 150,
    preference: "Veg"
  });
  const [plan, setPlan] = useState<any | null>(null);
  const [analysis, setAnalysis] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({
      ...prev,
      [name]: name === "patient_name" || name === "preference" ? value : Number(value)
    }));
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setAnalysis(null);
    try {
      const payload = {
        ...form,
        fasting_glucose: Number(form.fasting_glucose),
        hba1c: Number(form.hba1c),
        current_glucose: Number(form.current_glucose)
      };
      const data = await generateMealPlan(payload);
      setPlan(data);
    } catch (err: any) {
      setError(err?.message ?? "Failed to generate meal plan");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeConsumed = async () => {
    if (!plan) return;
    setLoading(true);
    setError(null);
    try {
      const meals = [
        ...(plan.breakfast ?? []),
        ...(plan.lunch ?? []),
        ...(plan.dinner ?? [])
      ].slice(0, 5);

      const payload = {
        patient_name: form.patient_name || "Anonymous",
        meals: meals.map((item: any) => ({
          food: item.food,
          quantity: 1
        }))
      };
      const data = await analyzeMeal(payload);
      setAnalysis(data);
    } catch (err: any) {
      setError(err?.message ?? "Failed to analyze meal");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card card-wide">
      <header className="card-header">
        <div>
          <h2>Module 1 – Smart Meal Planner</h2>
          <p className="subtitle">
            LLM + clinical guidelines + food database to build culturally appropriate Kerala meal plans.
          </p>
        </div>
      </header>

      <div className="card-body card-body-grid">
        <form className="form" onSubmit={handleGenerate}>
          <div className="form-row">
            <label>Patient name</label>
            <input
              name="patient_name"
              value={form.patient_name}
              onChange={onChange}
              placeholder="e.g. Anitha"
            />
          </div>
          <div className="form-row-two">
            <div>
              <label>Fasting glucose (mg/dL)</label>
              <input
                type="number"
                name="fasting_glucose"
                value={form.fasting_glucose}
                onChange={onChange}
              />
            </div>
            <div>
              <label>HbA1c (%)</label>
              <input
                type="number"
                step="0.1"
                name="hba1c"
                value={form.hba1c}
                onChange={onChange}
              />
            </div>
            <div>
              <label>Current glucose (mg/dL)</label>
              <input
                type="number"
                name="current_glucose"
                value={form.current_glucose}
                onChange={onChange}
              />
            </div>
          </div>
          <div className="form-row">
            <label>Diet preference</label>
            <select name="preference" value={form.preference} onChange={onChange}>
              <option value="Veg">Veg</option>
              <option value="Non-Veg">Non-Veg</option>
            </select>
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? "Working..." : "Generate 1‑day plan"}
            </button>
          </div>
          {error && <p className="error-text">{error}</p>}
        </form>

        <div className="plan-panel">
          {plan ? (
            <>
              <div className="plan-header">
                <h3>{plan.plan_type}</h3>
                <p className="chip">Patient: {plan.patient_name}</p>
              </div>
              <div className="plan-columns">
                {["breakfast", "lunch", "dinner"].map(mealKey => {
                  const list = plan[mealKey] ?? [];
                  return (
                    <div key={mealKey} className="plan-column">
                      <h4>{mealKey.charAt(0).toUpperCase() + mealKey.slice(1)}</h4>
                      <ul>
                        {list.map((item: any, idx: number) => (
                          <li key={idx}>
                            <div className="food-name">{item.food}</div>
                            <div className="food-meta">
                              <span>{item.quantity} ({item.quantity_grams} g)</span>
                              <span>GI {item.GI} · GL {item.GL}</span>
                            </div>
                            <p className="food-reason">{item.Reasoning}</p>
                          </li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
              </div>
              <button
                className="btn btn-secondary"
                type="button"
                onClick={handleAnalyzeConsumed}
                disabled={loading}
              >
                Analyze meal impact
              </button>
            </>
          ) : (
            <p className="placeholder">
              Generate a plan to see a structured, guideline‑aligned meal suggestion here.
            </p>
          )}

          {analysis && (
            <div className="analysis-panel">
              <h4>Post‑meal impact</h4>
              <p>
                Total meal GL: <strong>{analysis.total_meal_gl}</strong> ·
                Predicted 2‑hr glucose: <strong>{analysis.predicted_2hr_glucose}</strong> mg/dL ·
                Risk: <strong>{analysis.risk_assessment}</strong>
              </p>
              <ul>
                {analysis.analysis?.map((row: any, idx: number) => (
                  <li key={idx}>
                    <span className="food-name">{row.input}</span>
                    <span className="food-meta">
                      GI {row.GI} · GL {row.GL}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

