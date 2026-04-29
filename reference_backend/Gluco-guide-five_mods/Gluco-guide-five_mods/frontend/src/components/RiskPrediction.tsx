import React, { useState } from "react";
import { explainRisk } from "../api";

export const RiskPrediction: React.FC = () => {
  const [form, setForm] = useState({
    hba1c: 7.5,
    bmi: 28,
    age: 55,
    hypertension: 1,
    cholesterol: 210,
    smoker: 0,
    heart_disease: 0,
    phys_activity: 1
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
      const data = await explainRisk(form);
      setResult(data);
    } catch (err: any) {
      setError(err?.message ?? "Failed to compute complication risk");
    } finally {
      setLoading(false);
    }
  };

  const contributors = result?.contributors ?? [];

  return (
    <section className="card">
      <header className="card-header">
        <div>
          <h2>Module 3 – Long‑term Complication Risk</h2>
          <p className="subtitle">
            Hybrid ML + clinical rules estimate 5‑ and 10‑year risk for neuropathy, retinopathy and nephropathy.
          </p>
        </div>
      </header>
      <div className="card-body">
        <form className="form compact" onSubmit={handleSubmit}>
          <div className="form-row-two">
            <div>
              <label>HbA1c</label>
              <input type="number" step="0.1" name="hba1c" value={form.hba1c} onChange={onChange} />
            </div>
            <div>
              <label>BMI</label>
              <input type="number" name="bmi" value={form.bmi} onChange={onChange} />
            </div>
            <div>
              <label>Age</label>
              <input type="number" name="age" value={form.age} onChange={onChange} />
            </div>
          </div>

          <div className="form-row-two">
            <div>
              <label>Hypertension</label>
              <select name="hypertension" value={form.hypertension} onChange={onChange}>
                <option value={0}>No</option>
                <option value={1}>Yes</option>
              </select>
            </div>
            <div>
              <label>Cholesterol</label>
              <input type="number" name="cholesterol" value={form.cholesterol} onChange={onChange} />
            </div>
            <div>
              <label>Smoker</label>
              <select name="smoker" value={form.smoker} onChange={onChange}>
                <option value={0}>No</option>
                <option value={1}>Yes</option>
              </select>
            </div>
          </div>

          <div className="form-row-two">
            <div>
              <label>Heart disease</label>
              <select name="heart_disease" value={form.heart_disease} onChange={onChange}>
                <option value={0}>No</option>
                <option value={1}>Yes</option>
              </select>
            </div>
            <div>
              <label>Physical activity</label>
              <select name="phys_activity" value={form.phys_activity} onChange={onChange}>
                <option value={0}>Sedentary</option>
                <option value={1}>Regular</option>
              </select>
            </div>
          </div>

          <div className="form-actions">
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? "Calculating..." : "Estimate complication risk"}
            </button>
          </div>
          {error && <p className="error-text">{error}</p>}
        </form>

        {result && (
          <div className="risk-grid">
            <div className="risk-block">
              <h3>5‑year risk</h3>
              <p>
                Neuropathy: <strong>{result.neuropathy_5y}</strong>
              </p>
              <p>
                Retinopathy: <strong>{result.retinopathy_5y}</strong>
              </p>
              <p>
                Nephropathy: <strong>{result.nephropathy_5y}</strong>
              </p>
            </div>
            <div className="risk-block">
              <h3>10‑year risk</h3>
              <p>
                Neuropathy: <strong>{result.neuropathy_10y}</strong>
              </p>
              <p>
                Retinopathy: <strong>{result.retinopathy_10y}</strong>
              </p>
              <p>
                Nephropathy: <strong>{result.nephropathy_10y}</strong>
              </p>
            </div>
            <div className="risk-block">
              <h3>Key drivers</h3>
              <ul>
                {contributors.map((c: any, idx: number) => (
                  <li key={idx}>
                    <span className="feature-name">{c.feature}</span>
                    <span className="feature-impact">
                      Impact: {typeof c.impact === "number" ? c.impact.toFixed(3) : c.impact}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

