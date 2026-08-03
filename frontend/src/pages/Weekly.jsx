import { useEffect, useState } from "react";
import { getWeeklyDevices } from "../api/client";

function Weekly() {
  const [date, setDate] = useState(() => {
    const d = new Date();
    return d.toISOString().split("T")[0];
  });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = (selectedDate) => {
    setLoading(true);
    setError(null);
    getWeeklyDevices(selectedDate)
      .then(setData)
      .catch(() => setError("No se pudo cargar el resumen semanal."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load(date);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    load(date);
  };

  if (loading) return <p className="text-slate-500">Cargando...</p>;
  if (error) return <p className="text-red-600">{error}</p>;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <form onSubmit={handleSearch} className="bg-white rounded-lg shadow p-4 flex gap-2">
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="border rounded-md px-3 py-1.5 text-sm"
        />
        <button
          type="submit"
          className="bg-slate-900 text-white text-sm px-4 py-1.5 rounded-md hover:bg-slate-700"
        >
          Ver semana
        </button>
      </form>

      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h2 className="font-semibold text-slate-800">
            Comportamiento semanal ({data.week_start} al {data.week_end})
          </h2>
          <p className="text-sm text-slate-500">
            {data.devices.length} dispositivos consultados durante la semana.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-600 text-left">
              <tr>
                <th className="px-4 py-2">Modelo</th>
                <th className="px-4 py-2">IP</th>
                <th className="px-4 py-2 text-right">Dias en 0</th>
                <th className="px-4 py-2 text-right">Dias totales</th>
                <th className="px-4 py-2 text-right">Ultimo recuento</th>
                <th className="px-4 py-2 text-right">Maximo</th>
                <th className="px-4 py-2">Ultima captura</th>
              </tr>
            </thead>
            <tbody>
              {data.devices.map((d) => (
                <tr key={d.ip_address} className={`border-t ${d.is_alert ? "bg-red-50" : ""}`}>
                  <td className="px-4 py-2">{d.model_name}</td>
                  <td className="px-4 py-2 font-mono">{d.ip_address}</td>
                  <td className="px-4 py-2 text-right">{d.days_at_zero}</td>
                  <td className="px-4 py-2 text-right">{d.days_total}</td>
                  <td className="px-4 py-2 text-right">{d.last_page_count ?? "-"}</td>
                  <td className="px-4 py-2 text-right">{d.max_page_count ?? "-"}</td>
                  <td className="px-4 py-2">
                    {d.last_captured_at ? new Date(d.last_captured_at).toLocaleString() : "-"}
                  </td>
                </tr>
              ))}
              {data.devices.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-3 text-center text-slate-500">
                    Sin dispositivos en esa semana.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Weekly;
