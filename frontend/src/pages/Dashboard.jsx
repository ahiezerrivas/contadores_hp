import { useEffect, useMemo, useState } from "react";
import apiClient, { getDeviceHistory, getLatestRun, getRuns, triggerExport } from "../api/client";
import Modal from "../components/Modal.jsx";

function Dashboard() {
  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [runs, setRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(null);
  const [selectedRun, setSelectedRun] = useState(null);
  const [loadingSelected, setLoadingSelected] = useState(false);

  const [triggering, setTriggering] = useState(false);
  const [triggerError, setTriggerError] = useState(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [ipSearch, setIpSearch] = useState("");

  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyIp, setHistoryIp] = useState(null);
  const [historyDevice, setHistoryDevice] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const loadData = () => {
    getLatestRun()
      .then(setRun)
      .catch(() => setError("No se pudo cargar la informacion del ultimo run."))
      .finally(() => setLoading(false));

    getRuns()
      .then((data) => setRuns(data.results ?? data))
      .catch(() => {});
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTrigger = async () => {
    setTriggering(true);
    setTriggerError(null);
    try {
      await triggerExport();
      setSelectedRunId(null);
      setSelectedRun(null);
      loadData();
    } catch {
      setTriggerError("No se pudo ejecutar la consulta. Revisa la conexion a SQL Server.");
    } finally {
      setTriggering(false);
    }
  };

  const handleSelectRun = (runId) => {
    setSelectedRunId(runId);
    setSelectedRun(null);
    setIpSearch("");
    setModalOpen(true);
    setLoadingSelected(true);
    apiClient
      .get(`/runs/${runId}/`)
      .then((res) => setSelectedRun(res.data))
      .finally(() => setLoadingSelected(false));
  };

  const closeModal = () => {
    setModalOpen(false);
    setSelectedRunId(null);
    setSelectedRun(null);
  };

  const handleSelectDevice = (snapshot) => {
    setHistoryIp(snapshot.ip_address);
    setHistoryDevice(snapshot.display_name || snapshot.model_name);
    setHistoryData([]);
    setHistoryOpen(true);
    setLoadingHistory(true);
    getDeviceHistory(snapshot.ip_address)
      .then((result) => setHistoryData(result.results ?? result))
      .finally(() => setLoadingHistory(false));
  };

  const closeHistory = () => {
    setHistoryOpen(false);
    setHistoryIp(null);
    setHistoryDevice(null);
    setHistoryData([]);
  };

  const filteredSnapshots = useMemo(() => {
    const snapshots = selectedRun?.snapshots || [];
    const term = ipSearch.trim().toLowerCase();
    if (!term) return snapshots;
    return snapshots.filter((s) => s.ip_address.toLowerCase().includes(term));
  }, [selectedRun, ipSearch]);

  const devices = run?.snapshots || [];
  const alertCount = devices.filter((d) => d.is_alert).length;

  if (loading) return <p className="text-slate-500">Cargando...</p>;
  if (error) return <p className="text-red-600">{error}</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          {triggerError && <p className="text-red-600 text-sm">{triggerError}</p>}
        </div>
        <button
          type="button"
          onClick={handleTrigger}
          disabled={triggering}
          className="bg-slate-900 text-white text-sm px-4 py-2 rounded-md hover:bg-slate-700 disabled:opacity-50"
        >
          {triggering ? "Consultando..." : "Volver a consultar"}
        </button>
      </div>

      {!run ? (
        <p className="text-slate-500">Aun no hay ejecuciones registradas.</p>
      ) : (
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Total dispositivos" value={run.total_devices} />
        <StatCard
          label="Ultima ejecucion"
          value={new Date(run.executed_at).toLocaleString()}
          small
        />
        <StatCard label="Alertas (paginas en 0)" value={alertCount} danger={alertCount > 0} />
      </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h2 className="font-semibold text-slate-800">Historial de consultas</h2>
          <p className="text-sm text-slate-500">
            Cada vez que se ejecuta el export se guarda la fecha/hora y la info de los
            dispositivos consultados. Haz clic en una fila para ver el detalle.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-600 text-left">
              <tr>
                <th className="px-4 py-2">Fecha y hora</th>
                <th className="px-4 py-2 text-right">Dispositivos</th>
                <th className="px-4 py-2">Estado</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => handleSelectRun(r.id)}
                  className="border-t hover:bg-slate-50 cursor-pointer"
                >
                  <td className="px-4 py-2">{new Date(r.executed_at).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right">{r.total_devices}</td>
                  <td className="px-4 py-2">
                    {r.success ? (
                      <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-700 text-xs font-medium">
                        OK
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded bg-red-100 text-red-700 text-xs font-medium">
                        Error
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Modal
        open={modalOpen}
        onClose={closeModal}
        title="Detalle de la consulta"
        subtitle={selectedRun ? new Date(selectedRun.executed_at).toLocaleString() : ""}
      >
        <input
          type="text"
          placeholder="Buscar por IP..."
          value={ipSearch}
          onChange={(e) => setIpSearch(e.target.value)}
          className="border rounded-md px-3 py-1.5 text-sm w-full mb-3"
        />
        {loadingSelected ? (
          <p className="text-slate-500">Cargando detalle...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border">
              <thead className="bg-slate-50 text-slate-600 text-left">
                <tr>
                  <th className="px-3 py-1.5">Modelo</th>
                  <th className="px-3 py-1.5">Nombre</th>
                  <th className="px-3 py-1.5">IP</th>
                  <th className="px-3 py-1.5 text-right">Paginas</th>
                  <th className="px-3 py-1.5">Severidad</th>
                  <th className="px-3 py-1.5">Numero de serie</th>
                  <th className="px-3 py-1.5">Ubicacion</th>
                </tr>
              </thead>
              <tbody>
                {filteredSnapshots.map((s) => (
                  <tr
                    key={s.id}
                    onClick={() => handleSelectDevice(s)}
                    className="border-t hover:bg-slate-50 cursor-pointer"
                    title="Ver historico de este dispositivo"
                  >
                    <td className="px-3 py-1.5">{s.model_name}</td>
                    <td className="px-3 py-1.5">{s.display_name}</td>
                    <td className="px-3 py-1.5 font-mono">{s.ip_address}</td>
                    <td className="px-3 py-1.5 text-right">
                      {s.page_count === null ? "-" : s.page_count.toLocaleString()}
                    </td>
                    <td className="px-3 py-1.5">{s.device_status_severity || "-"}</td>
                    <td className="px-3 py-1.5 font-mono">{s.serial_number || "-"}</td>
                    <td className="px-3 py-1.5">{s.system_location || "-"}</td>
                  </tr>
                ))}
                {filteredSnapshots.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-3 py-3 text-center text-slate-500">
                      Sin resultados.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Modal>

      <Modal
        open={historyOpen}
        onClose={closeHistory}
        title={`Historico - ${historyDevice ?? ""}`}
        subtitle={historyIp}
      >
        {loadingHistory ? (
          <p className="text-slate-500">Cargando historico...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border">
              <thead className="bg-slate-50 text-slate-600 text-left">
                <tr>
                  <th className="px-3 py-1.5">Fecha</th>
                  <th className="px-3 py-1.5 text-right">Paginas (acumulado)</th>
                  <th className="px-3 py-1.5 text-right">Impresas desde captura anterior</th>
                </tr>
              </thead>
              <tbody>
                {historyData
                  .slice()
                  .reverse()
                  .map((h) => (
                    <tr key={h.id} className="border-t">
                      <td className="px-3 py-1.5">{new Date(h.captured_at).toLocaleString()}</td>
                      <td className="px-3 py-1.5 text-right">
                        {h.page_count === null ? "-" : h.page_count.toLocaleString()}
                      </td>
                      <td className="px-3 py-1.5 text-right">
                        {h.printed_since_previous === null || h.printed_since_previous === undefined
                          ? "-"
                          : h.printed_since_previous.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                {historyData.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-3 py-3 text-center text-slate-500">
                      Sin historico para este dispositivo.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Modal>
    </div>
  );
}

function StatCard({ label, value, small, danger }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p
        className={`mt-1 font-semibold ${danger ? "text-red-600" : "text-slate-900"} ${
          small ? "text-base" : "text-2xl"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

export default Dashboard;
