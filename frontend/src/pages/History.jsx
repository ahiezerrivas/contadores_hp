import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getDeviceHistory } from "../api/client";

function History() {
  const [ip, setIp] = useState("");
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!ip.trim()) return;
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const result = await getDeviceHistory(ip.trim());
      setData(result.results ?? result);
    } catch {
      setError("No se pudo cargar el historico para esa IP.");
    } finally {
      setLoading(false);
    }
  };

  const chartData = data.map((d) => ({
    fecha: new Date(d.captured_at).toLocaleDateString(),
    paginas: d.page_count,
  }));

  const weeklyDeltas = data
    .map((d, idx) => ({
      from: idx > 0 ? new Date(data[idx - 1].captured_at).toLocaleDateString() : null,
      to: new Date(d.captured_at).toLocaleDateString(),
      delta: d.printed_since_previous,
    }))
    .filter((row) => row.delta !== null && row.delta !== undefined)
    .reverse();

  return (
    <div className="space-y-6">
      <form onSubmit={handleSearch} className="bg-white rounded-lg shadow p-4 flex gap-2">
        <input
          type="text"
          placeholder="IP del dispositivo (ej. 10.10.65.200)"
          value={ip}
          onChange={(e) => setIp(e.target.value)}
          className="border rounded-md px-3 py-1.5 text-sm flex-1"
        />
        <button
          type="submit"
          className="bg-slate-900 text-white text-sm px-4 py-1.5 rounded-md hover:bg-slate-700"
        >
          Buscar
        </button>
      </form>

      {loading && <p className="text-slate-500">Cargando...</p>}
      {error && <p className="text-red-600">{error}</p>}

      {!loading && searched && data.length === 0 && !error && (
        <p className="text-slate-500">Sin datos historicos para esa IP.</p>
      )}

      {data.length > 0 && (
        <>
          <div className="bg-white rounded-lg shadow p-4">
            <h2 className="font-semibold text-slate-800 mb-4">
              Tendencia de recuento de paginas - {ip}
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="fecha" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line type="monotone" dataKey="paginas" stroke="#0f172a" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h2 className="font-semibold text-slate-800">Comportamiento semanal</h2>
              <p className="text-sm text-slate-500">
                Paginas impresas entre capturas consecutivas. Un delta de 0 puede indicar que el
                dispositivo estuvo inactivo o sin conexion.
              </p>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-600 text-left">
                <tr>
                  <th className="px-4 py-2">Desde</th>
                  <th className="px-4 py-2">Hasta</th>
                  <th className="px-4 py-2 text-right">Paginas impresas</th>
                  <th className="px-4 py-2">Estado</th>
                </tr>
              </thead>
              <tbody>
                {weeklyDeltas.map((row, idx) => (
                  <tr key={idx} className="border-t hover:bg-slate-50">
                    <td className="px-4 py-2">{row.from}</td>
                    <td className="px-4 py-2">{row.to}</td>
                    <td className="px-4 py-2 text-right">{row.delta}</td>
                    <td className="px-4 py-2">
                      {row.delta === 0 ? (
                        <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-700 text-xs font-medium">
                          Sin actividad
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-700 text-xs font-medium">
                          Activo
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

export default History;
