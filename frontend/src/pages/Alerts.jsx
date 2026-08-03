import { useEffect, useState } from "react";
import { getAlerts } from "../api/client";

function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getAlerts()
      .then((data) => setAlerts(data.results ?? data))
      .catch(() => setError("No se pudieron cargar las alertas."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-slate-500">Cargando...</p>;
  if (error) return <p className="text-red-600">{error}</p>;

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b">
        <h2 className="font-semibold text-slate-800">
          Dispositivos con recuento de paginas en 0 o desconocido
        </h2>
        <p className="text-sm text-slate-500">
          Basado en la ultima ejecucion del export. Revisa conectividad o estado del dispositivo.
        </p>
      </div>
      {alerts.length === 0 ? (
        <p className="p-4 text-slate-500">No hay alertas activas.</p>
      ) : (
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600 text-left">
            <tr>
              <th className="px-4 py-2">Modelo</th>
              <th className="px-4 py-2">IP</th>
              <th className="px-4 py-2 text-right">Paginas</th>
              <th className="px-4 py-2">Capturado</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((d) => (
              <tr key={d.id} className="border-t hover:bg-red-50">
                <td className="px-4 py-2">{d.model_name}</td>
                <td className="px-4 py-2 font-mono">{d.ip_address}</td>
                <td className="px-4 py-2 text-right">{d.page_count ?? "-"}</td>
                <td className="px-4 py-2">{new Date(d.captured_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default Alerts;
