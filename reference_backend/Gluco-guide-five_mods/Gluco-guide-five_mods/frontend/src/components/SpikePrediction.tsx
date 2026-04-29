import React, { useState } from "react";
import { predictSpike } from "../api";

export const SpikePrediction: React.FC = () => {
  const [form, setForm] = useState({
    current_glucose: 160,
    avg_GI: 55,
    total_GL: 40,
    duration_years: 8,
    age: 52,
    bmi: 27.5,
    activity_level: 1,
    medication_dose: 1000,
    hba1c: 7.5,
    bp_systolic: 130,
    bp_diastolic: 82,
    cholesterol: 190,
    fasting_glucose: 135,
    time_of_day: 0,
    family_history: 1,
    alcohol_smoking: 0
  });
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({
      ...prev,
      [name]: Number(value)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await predictSpike(form);
      setResult(data);
    } catch (err: any) {
      setError(err?.message ?? "Failed to predict spike");
    } finally {
      setLoading(false);
    }
  };

  const predictions = result?.predictions ?? {};

  return (
    <section className="card">
      <header className="card-header">
        <div>
          <h2>Module 2 – Post‑meal Spike Prediction</h2>
          <p className="subtitle">
            Random Forest model forecasts glucose at 30–120 minutes and flags risky spikes.
          </p>
        </div>
      </header>
      <div className="card-body">
        <form className="form compact" onSubmit={handleSubmit}>
          <div className="form-row-two">
            <div>
              <label>Current glucose</label>
              <input
                type="number"
                name="current_glucose"
                value={form.current_glucose}
                onChange={onChange}
              />
            </div>
            <div>
              <label>Avg GI</label>
              <input type="number" name="avg_GI" value={form.avg_GI} onChange={onChange} />
            </div>
            <div>
              <label>Total GL</label>
              <input type="number" name="total_GL" value={form.total_GL} onChange={onChange} />
            </div>
          </div>

          <div className="form-row-two">
            <div>
              <label>Age</label>
              <input type="number" name="age" value={form.age} onChange={onChange} />
            </div>
            <div>
              <label>BMI</label>
              <input type="number" name="bmi" value={form.bmi} onChange={onChange} />
            </div>
            <div>
              <label>HbA1c</label>
              <input type="number" step="0.1" name="hba1c" value={form.hba1c} onChange={onChange} />
            </div>
          </div>

          <div className="form-row-two">
            <div>
              <label>Activity level</label>
              <select name="activity_level" value={form.activity_level} onChange={onChange}>
                <option value={0}>Active</option>
                <option value={1}>Sedentary</option>
              </select>
            </div>
            <div>
              <label>Time of day</label>
              <select name="time_of_day" value={form.time_of_day} onChange={onChange}>
                <option value={0}>Morning</option>
                <option value={1}>Evening</option>
              </select>
            </div>
            <div>
              <label>Medication dose (mg)</label>
              <input
                type="number"
                name="medication_dose"
                value={form.medication_dose}
                onChange={onChange}
              />
            </div>
          </div>

          <div className="form-row-two">
            <div>
              <label>BP systolic</label>
              <input
                type="number"
                name="bp_systolic"
                value={form.bp_systolic}
                onChange={onChange}
              />
            </div>
            <div>
              <label>BP diastolic</label>
              <input
                type="number"
                name="bp_diastolic"
                value={form.bp_diastolic}
                onChange={onChange}
              />
            </div>
            <div>
              <label>Cholesterol</label>
              <input
                type="number"
                name="cholesterol"
                value={form.cholesterol}
                onChange={onChange}
              />
            </div>
          </div>

          <div className="form-row-two">
            <div>
              <label>Fasting glucose</label>
              <input
                type="number"
                name="fasting_glucose"
                value={form.fasting_glucose}
                onChange={onChange}
              />
            </div>
            <div>
              <label>Family history</label>
              <select name="family_history" value={form.family_history} onChange={onChange}>
                <option value={0}>No</option>
                <option value={1}>Yes</option>
              </select>
            </div>
            <div>
              <label>Alcohol/smoking</label>
              <select name="alcohol_smoking" value={form.alcohol_smoking} onChange={onChange}>
                <option value={0}>No</option>
                <option value={1}>Yes</option>
              </select>
            </div>
          </div>

          <div className="form-actions">
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? "Predicting..." : "Predict 2‑hour profile"}
            </button>
          </div>
          {error && <p className="error-text">{error}</p>}
        </form>

        {result && (
          <div className="chart-card">
            <h3>Predicted glucose curve</h3>
            <div className="sparkline">
              {["30min", "60min", "90min", "120min"].map(step => (
                <div key={step} className="sparkline-point">
                  <div className="sparkline-bar">
                    <div
                      className="sparkline-fill"
                      style={{
                        height: `${Math.min(260, Math.max(60, predictions[step] || 0)) / 3}%`
                      }}
                    />
                  </div>
                  <span className="sparkline-label">
                    {step}
                    <br />
                    {predictions[step]}
                  </span>
                </div>
              ))}
            </div>
            <p className="risk-chip">
              Spike risk: <strong>{result.spike_risk}</strong> – {result.advice}
            </p>
          </div>
        )}
      </div>
    </section>
  );
};

