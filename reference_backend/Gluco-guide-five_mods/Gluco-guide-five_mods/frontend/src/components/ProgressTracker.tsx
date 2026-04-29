import React, { useEffect, useState } from "react";
import { analyzeTracker, explainTrend, getQuestions } from "../api";

type QuestionMap = Record<
  string,
  {
    question: string;
    options: Record<string, number>;
  }
>;

const diseases = [
  { id: "neuropathy", label: "Neuropathy" },
  { id: "retinopathy", label: "Retinopathy" },
  { id: "nephropathy", label: "Nephropathy" }
];

export const ProgressTracker: React.FC = () => {
  const [patientId, setPatientId] = useState("patient123");
  const [disease, setDisease] = useState("neuropathy");
  const [questions, setQuestions] = useState<QuestionMap>({});
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<any | null>(null);
  const [trendOnly, setTrendOnly] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setError(null);
        const data = await getQuestions(disease);
        setQuestions(data);
        const initial: Record<string, number> = {};
        Object.keys(data).forEach(key => {
          const opts = data[key].options;
          const firstValue = Object.values(opts)[0] ?? 0;
          initial[key] = firstValue;
        });
        setAnswers(initial);
        setResult(null);
        setTrendOnly(null);
      } catch (err: any) {
        setError(err?.message ?? "Failed to load questions");
      }
    };
    load();
  }, [disease]);

  const handleOptionChange = (qid: string, score: number) => {
    setAnswers(prev => ({ ...prev, [qid]: score }));
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeTracker(patientId, disease, answers);
      setResult(data);
    } catch (err: any) {
      setError(err?.message ?? "Failed to analyze disease trend");
    } finally {
      setLoading(false);
    }
  };

  const handleTrendOnly = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await explainTrend(patientId, disease);
      setTrendOnly(data);
    } catch (err: any) {
      setError(err?.message ?? "Failed to fetch trend explanation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card card-tall">
      <header className="card-header">
        <div>
          <h2>Module 4 – Disease Progress Tracker</h2>
          <p className="subtitle">
            Structured symptom surveys converted into longitudinal risk scores, ML forecasts and plain‑language explanations.
          </p>
        </div>
      </header>
      <div className="card-body card-body-grid">
        <div className="tracker-form">
          <div className="form-row-two">
            <div>
              <label>Patient ID</label>
              <input value={patientId} onChange={e => setPatientId(e.target.value)} />
            </div>
            <div>
              <label>Disease focus</label>
              <select value={disease} onChange={e => setDisease(e.target.value)}>
                {diseases.map(d => (
                  <option key={d.id} value={d.id}>
                    {d.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="question-list">
            {Object.entries(questions).map(([qid, q]) => (
              <div key={qid} className="question-item">
                <p className="question-text">{q.question}</p>
                <div className="pill-row">
                  {Object.entries(q.options).map(([label, val]) => (
                    <button
                      key={label}
                      type="button"
                      className={
                        answers[qid] === val ? "pill pill-selected" : "pill"
                      }
                      onClick={() => handleOptionChange(qid, val)}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="form-actions">
            <button className="btn btn-primary" type="button" disabled={loading} onClick={handleAnalyze}>
              {loading ? "Scoring..." : "Save visit & compute score"}
            </button>
            <button className="btn btn-ghost" type="button" disabled={loading} onClick={handleTrendOnly}>
              Show trend‑only explanation
            </button>
          </div>
          {error && <p className="error-text">{error}</p>}
        </div>

        <div className="tracker-results">
          {result ? (
            <>
              <div className="score-header">
                <h3>
                  {result.status} · <span className="chip">{result.trend}</span>
                </h3>
                <p>
                  Current normalized score: <strong>{result.score}</strong>
                </p>
              </div>
              <div className="score-columns">
                <div>
                  <h4>Interpretation</h4>
                  <ul>
                    {result.interpretation?.map((t: string, idx: number) => (
                      <li key={idx}>{t}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4>Recommendations</h4>
                  <ul>
                    {result.recommendations?.map((t: string, idx: number) => (
                      <li key={idx}>{t}</li>
                    ))}
                  </ul>
                </div>
              </div>
              {result.forecast && (
                <div className="forecast-panel">
                  <h4>Forecast</h4>
                  <pre>{JSON.stringify(result.forecast, null, 2)}</pre>
                  <p className="explanation">{result.explanation}</p>
                </div>
              )}
            </>
          ) : (
            <p className="placeholder">
              Answer questions and save a visit to see the risk trajectory and personalized advice here.
            </p>
          )}

          {trendOnly && !result && (
            <div className="forecast-panel">
              <h4>Trend only</h4>
              <pre>{JSON.stringify(trendOnly.forecast, null, 2)}</pre>
              <p className="explanation">{trendOnly.explanation}</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

