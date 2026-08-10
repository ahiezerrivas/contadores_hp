import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8001/api",
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export const login = (credentials) =>
  apiClient.post("/auth/login/", credentials).then((r) => r.data);

export const me = () => apiClient.get("/auth/me/").then((r) => r.data);

export const getLatestRun = () => apiClient.get("/runs/latest/").then((r) => r.data);

export const getLatestDevices = (params = {}) =>
  apiClient.get("/devices/latest/", { params }).then((r) => r.data);

export const getAlerts = () => apiClient.get("/devices/alerts/").then((r) => r.data);

export const getDeviceHistory = (ipAddress) =>
  apiClient.get("/devices/history/", { params: { ip_address: ipAddress } }).then((r) => r.data);

export const getRuns = () => apiClient.get("/runs/").then((r) => r.data);

export const triggerExport = () => apiClient.post("/runs/trigger/").then((r) => r.data);

export const getWeeklyDevices = (date) =>
  apiClient.get("/devices/weekly/", { params: date ? { date } : {} }).then((r) => r.data);

export const getMonthlyCounters = (params = {}) =>
  apiClient.get("/monthly-counters/", { params }).then((r) => r.data);

export const exportMonthlyCounters = (params = {}) =>
  apiClient
    .get("/monthly-counters/export/", { params, responseType: "blob" })
    .then((r) => r.data);

export const getMonthlyCounterFilters = (params = {}) =>
  apiClient.get("/monthly-counters/filters/", { params }).then((r) => r.data);

export const getMonthlyCountersByPeriod = (params = {}) =>
  apiClient.get("/monthly-counters/by-period/", { params }).then((r) => r.data);

export const updateMonthlyCounter = (id, data) =>
  apiClient.patch(`/monthly-counters/${id}/`, data).then((r) => r.data);

export const getMissingSnapshots = (params = {}) =>
  apiClient.get("/monthly-counters/missing_snapshots/", { params }).then((r) => r.data);

export const updateImpresoraStatus = (impresoraId, status) =>
  apiClient
    .patch("/monthly-counters/impresora-status/", { impresora_id: impresoraId, status })
    .then((r) => r.data);

export const pingDevice = (ipAddress) =>
  apiClient.get("/devices/ping/", { params: { ip_address: ipAddress } }).then((r) => r.data);

export const getOficinas = (params = {}) =>
  apiClient.get("/oficinas/", { params }).then((r) => r.data);

export const createOficina = (data) =>
  apiClient.post("/oficinas/", data).then((r) => r.data);

export const updateOficina = (id, data) =>
  apiClient.patch(`/oficinas/${id}/`, data).then((r) => r.data);

export const deleteOficina = (id) =>
  apiClient.delete(`/oficinas/${id}/`).then((r) => r.data);

export const getImpresoras = (params = {}) =>
  apiClient.get("/impresoras/", { params }).then((r) => r.data);

export const createImpresora = (data) =>
  apiClient.post("/impresoras/", data).then((r) => r.data);

export const updateImpresora = (id, data) =>
  apiClient.patch(`/impresoras/${id}/`, data).then((r) => r.data);

export const deleteImpresora = (id) =>
  apiClient.delete(`/impresoras/${id}/`).then((r) => r.data);

export default apiClient;
