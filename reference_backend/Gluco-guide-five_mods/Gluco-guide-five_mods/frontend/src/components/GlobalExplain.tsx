import React, { useState } from "react";
import { explainGlobal } from "../api";

export const GlobalExplain: React.FC = () => {
  const [patientId, setPatientId] = useState("patient123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        patient_id: patientId,
        spike_data: {
          current_glucose: 165,
          avg_GI: 58,
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
        },
        risk_data: {
          hba1c: 7.5,
          bmi: 28,
          age: 55,
          hypertension: 1,
          cholesterol: 210,
          smoker: 0,
          heart_disease: 0,
          phys_activity: 1
        }
      };
      const data = await explainGlobal(payload);
      setResult(data);
    } catch (err: any) {
      setError(err?.message ?? "Failed to aggregate explanations");
    } finally {
      setLoading(false);
    }
  };

  const spikeTop = result?.spike_explanation?.contributors?.[0];
  const riskTop = result?.risk_explanation?.contributors?.[0];

  return (
    <section className="card card-wide">
      <header className="card-header">
        <div>
          <h2>Module 5 – Explainable AI Overview</h2>
          <p className="subtitle">
            Combines spike drivers, chronic risk factors and symptom trends into an executive summary you can discuss with patients.
          </p>
        </div>
      </header>
      <div className="card-body">
        <div className="form-row-two">
          <div>
            <label>Patient ID</label>
            <input value={patientId} onChange={e => setPatientId(e.target.value)} />
          </div>
          <div className="form-actions-inline">
            <button className="btn btn-primary" type="button" disabled={loading} onClick={handleRun}>
              {loading ? "Aggregating..." : "Generate global explanation"}
            </button>
          </div>
        </div>
        {error && <p className="error-text">{error}</p>}

        {result && (
          <div className="global-layout">
            <div className="summary-panel">
              <h3>Executive summary</h3>
              <p>{result.executive_summary || "No summary available."}</p>

              <div className="chips-row">
                {spikeTop && (
                  <span className="chip">
                    Spike: {spikeTop.feature} ({spikeTop.impact?.toFixed?.(2) ?? spikeTop.impact})
                  </span>
                )}
                {riskTop && (
                  <span className="chip">
                    Long‑term: {riskTop.feature} ({riskTop.impact?.toFixed?.(2) ?? riskTop.impact})
                  </span>
                )}
              </div>
            </div>

            <div className="global-columns">
              <div className="global-column">
                <h4>Immediate spike drivers</h4>
                <ul>
                  {result.spike_explanation?.contributors?.map((c: any, idx: number) => (
                    <li key={idx}>
                      <span className="feature-name">{c.feature}</span>
                      <span className="feature-impact">
                        {typeof c.impact === "number" ? c.impact.toFixed(3) : c.impact}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="global-column">
                <h4>Chronic risk drivers</h4>
                <ul>
                  {result.risk_explanation?.contributors?.map((c: any, idx: number) => (
                    <li key={idx}>
                      <span className="feature-name">{c.feature}</span>
                      <span className="feature-impact">
                        {typeof c.impact === "number" ? c.impact.toFixed(3) : c.impact}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="global-column">
                <h4>Complication trajectories</h4>
                <ul>
                  {Object.entries(result.progression_explanation || {}).map(([disease, payload]) => (
                    <li key={disease}>
                      <strong>{disease}</strong>
                      <p className="small">
                        History points: {(payload as any).history_points ?? "?"}
                      </p>
                      <p className="small">
                        Explanation: {(payload as any).explanation ?? "N/A"}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

