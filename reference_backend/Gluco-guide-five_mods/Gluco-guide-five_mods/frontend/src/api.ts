import axios from "axios";

// Back-end module base URLs
// These ports follow the actual FastAPI configurations (not just the batch file comments).
export const MODULE_1_URL = "http://127.0.0.1:8001";
export const MODULE_2_URL = "http://127.0.0.1:8003";
export const MODULE_3_URL = "http://127.0.0.1:8004";
export const MODULE_4_URL = "http://127.0.0.1:8005";
export const MODULE_5_URL = "http://127.0.0.1:8006";

const client = axios.create({
  timeout: 15000
});

export async function generateMealPlan(payload: any) {
  const res = await client.post(`${MODULE_1_URL}/generate-meal-plan/`, payload);
  return res.data;
}

export async function analyzeMeal(payload: any) {
  const res = await client.post(`${MODULE_1_URL}/analyze-consumed-meal/`, payload);
  return res.data;
}

export async function predictSpike(payload: any) {
  const res = await client.post(`${MODULE_2_URL}/predict-spike/`, payload);
  return res.data;
}

export async function explainSpike(payload: any) {
  // Module 5 uses GET with JSON body for /explain-spike/
  const res = await client.get(`${MODULE_2_URL}/explain-spike/`, {
    data: payload
  } as any);
  return res.data;
}

export async function explainRisk(payload: any) {
  const res = await client.post(`${MODULE_3_URL}/explain-risk-json/`, payload);
  return res.data;
}

export async function getQuestions(disease: string) {
  const res = await client.get(`${MODULE_4_URL}/questions/${disease}`);
  return res.data;
}

export async function analyzeTracker(patientId: string, disease: string, answers: Record<string, number>) {
  const res = await client.post(`${MODULE_4_URL}/analyze/${patientId}/${disease}`, { answers });
  return res.data;
}

export async function explainTrend(patientId: string, disease: string) {
  const res = await client.get(`${MODULE_4_URL}/explain-trend/${patientId}/${disease}`);
  return res.data;
}

export async function explainGlobal(payload: any) {
  const res = await client.post(`${MODULE_5_URL}/explain/global`, payload);
  return res.data;
}

