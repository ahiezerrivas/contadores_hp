import { useEffect, useState } from "react";
import { getRuns } from "../api/client";

function Runs() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getRuns()
      .then((data) => setRuns(data.results ?? data))
      .catch(() => setError("No se pudo cargar el historial de ejecuciones."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-slate-500">Cargando...</p>;
  if (error) return <p className="text-red-600">{error}</p>;

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b">
        <h2 className="font-semibold text-slate-800">Historial de ejecuciones del export</h2>
      </div>
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-slate-600 text-left">
          <tr>
            <th className="px-4 py-2">Fecha</th>
            <th className="px-4 py-2 text-right">Dispositivos</th>
            <th className="px-4 py-2">Estado</th>
            <th className="px-4 py-2">Error</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr key={r.id} className="border-t hover:bg-slate-50">
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
              <td className="px-4 py-2 text-slate-500">{r.error_message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Runs;
