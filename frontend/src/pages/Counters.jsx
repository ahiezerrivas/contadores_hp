import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  exportMonthlyCounters,
  getMissingSnapshots,
  getMonthlyCounterFilters,
  getMonthlyCounters,
  getMonthlyCountersByPeriod,
  pingDevice,
  updateImpresoraStatus,
  updateMonthlyCounter,
} from "../api/client";
import Modal from "../components/Modal.jsx";

const ALL = "__all__";

function FilterSelect({ label, value, onChange, options }) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-slate-500 text-xs uppercase tracking-wide">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border rounded-md px-3 py-1.5 text-sm bg-white"
      >
        <option value={ALL}>Todo</option>
        {options.map((opt) => {
          const isObj = opt && typeof opt === "object";
          const optValue = isObj ? String(opt.id ?? opt.value ?? "") : opt;
          const optLabel = isObj ? (opt.name ?? opt.label ?? optValue) : opt;
          return (
            <option key={optValue} value={optValue}>
              {optLabel}
            </option>
          );
        })}
      </select>
    </label>
  );
}

function formatNumber(value) {
  return value === null || value === undefined ? "-" : value.toLocaleString();
}

function Counters({ isAdmin = false }) {
  const [filters, setFilters] = useState({ regions: [], categories: [], periods: [], printer_statuses: [], offices: [] });

  const [region, setRegion] = useState(ALL);
  const [category, setCategory] = useState(ALL);
  const [period, setPeriod] = useState(ALL);
  const [printerStatus, setPrinterStatus] = useState(ALL);
  const [office, setOffice] = useState(ALL);
  const [search, setSearch] = useState("");

  const [data, setData] = useState({ count: 0, next: null, previous: null, results: [] });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selected, setSelected] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [ordering, setOrdering] = useState("");

  const [missing, setMissing] = useState({ count: 0, results: [], days: 5 });
  const [missingOpen, setMissingOpen] = useState(false);
  const [pingStatus, setPingStatus] = useState({});
  const [savingStatusId, setSavingStatusId] = useState(null);
  const [allStatuses, setAllStatuses] = useState([]);
  const [tooltip, setTooltip] = useState({ visible: false, text: "", x: 0, y: 0 });
  const [exporting, setExporting] = useState(false);
  const [periodData, setPeriodData] = useState([]);
  const [chartLoading, setChartLoading] = useState(false);

  useEffect(() => {
    getMonthlyCounterFilters({})
      .then((data) => setAllStatuses(data.printer_statuses || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    setForm(selected);
    setEditing(false);
    setSaveError(null);
  }, [selected]);

  const handleFieldChange = (name, value) => {
    setForm((f) => ({ ...f, [name]: value }));
  };

  const handleExport = () => {
    setExporting(true);
    const params = {};
    if (region !== ALL) params.region = region;
    if (category !== ALL) params.category = category;
    if (period !== ALL) params.period = period;
    if (printerStatus !== ALL) params.printer_status = printerStatus;
    if (office !== ALL) params.office = office;
    if (search.trim()) params.search = search.trim();

    exportMonthlyCounters(params)
      .then((blob) => {
        const url = window.URL.createObjectURL(new Blob([blob]));
        const a = document.createElement("a");
        a.href = url;
        a.download = "contadores.xlsx";
        a.click();
        window.URL.revokeObjectURL(url);
      })
      .catch(() => alert("No se pudo generar el archivo Excel."))
      .finally(() => setExporting(false));
  };

  const handleSave = () => {
    setSaving(true);
    setSaveError(null);
    updateMonthlyCounter(selected.id, form)
      .then((updated) => {
        setSelected(updated);
        setData((d) => ({
          ...d,
          results: d.results.map((r) => (r.id === updated.id ? updated : r)),
        }));
        setEditing(false);
      })
      .catch(() => setSaveError("No se pudieron guardar los cambios."))
      .finally(() => setSaving(false));
  };

  const handleCancelEdit = () => {
    setForm(selected);
    setEditing(false);
    setSaveError(null);
  };

  useEffect(() => {
    const params = {};
    if (region !== ALL) params.region = region;
    if (category !== ALL) params.category = category;
    if (period !== ALL) params.period = period;
    if (printerStatus !== ALL) params.printer_status = printerStatus;
    if (office !== ALL) params.office = office;

    getMonthlyCounterFilters(params)
      .then(setFilters)
      .catch(() => {});
  }, [region, category, period, printerStatus, office]);

  const fetchMissing = () => {
    const params = { printer_status: "Instalado" };
    if (region !== ALL) params.region = region;
    if (category !== ALL) params.category = category;
    if (period !== ALL) params.period = period;
    if (office !== ALL) params.office = office;

    getMissingSnapshots(params)
      .then(setMissing)
      .catch(() => {});
  };

  useEffect(fetchMissing, [region, category, period, office]);

  const handleStatusChange = (impresoraId, newStatus) => {
    setSavingStatusId(impresoraId);
    updateImpresoraStatus(impresoraId, newStatus)
      .then(() => {
        fetchMissing();
      })
      .catch(() => {})
      .finally(() => setSavingStatusId(null));
  };

  const handlePing = (ipAddress) => {
    setPingStatus((s) => ({ ...s, [ipAddress]: "loading" }));
    pingDevice(ipAddress)
      .then((res) => {
        setPingStatus((s) => ({ ...s, [ipAddress]: res.reachable ? "up" : "down" }));
      })
      .catch(() => {
        setPingStatus((s) => ({ ...s, [ipAddress]: "error" }));
      });
  };

  useEffect(() => {
    setLoading(true);
    setError(null);
    const params = { page };
    if (region !== ALL) params.region = region;
    if (category !== ALL) params.category = category;
    if (period !== ALL) params.period = period;
    if (printerStatus !== ALL) params.printer_status = printerStatus;
    if (office !== ALL) params.office = office;
    if (search.trim()) params.search = search.trim();
    if (ordering) params.ordering = ordering;

    getMonthlyCounters(params)
      .then(setData)
      .catch(() => setError("No se pudieron cargar los contadores."))
      .finally(() => setLoading(false));
  }, [region, category, period, printerStatus, office, search, page, ordering]);

  const resetToFirstPage = (setter) => (value) => {
    setPage(1);
    setter(value);
  };

  const totalPages = useMemo(() => Math.max(1, Math.ceil(data.count / 50)), [data.count]);

  const totalMonthly = useMemo(
    () => data.results.reduce((sum, e) => sum + (Number(e.monthly_counter) || 0), 0),
    [data.results]
  );

  useEffect(() => {
    setChartLoading(true);
    const params = {};
    if (region !== ALL) params.region = region;
    if (category !== ALL) params.category = category;
    if (period !== ALL) params.period = period;
    if (printerStatus !== ALL) params.printer_status = printerStatus;
    if (office !== ALL) params.office = office;
    if (search.trim()) params.search = search.trim();

    getMonthlyCountersByPeriod(params)
      .then((data) => setPeriodData(data))
      .catch(() => setPeriodData([]))
      .finally(() => setChartLoading(false));
  }, [region, category, period, printerStatus, office, search]);

  const SortHeader = ({ field, children, align = "left" }) => {
    const isAsc = ordering === field;
    const isDesc = ordering === `-${field}`;
    const arrow = isAsc ? "▲" : isDesc ? "▼" : "";
    const alignClass = align === "right" ? "text-right" : "text-left";
    return (
      <th
        onClick={() => {
          setPage(1);
          if (isAsc) setOrdering(`-${field}`);
          else setOrdering(field);
        }}
        className={`px-2 py-2 truncate cursor-pointer select-none hover:bg-slate-100 ${alignClass}`}
      >
        <span className="inline-flex items-center gap-1">
          {children} {arrow}
        </span>
      </th>
    );
  };

  return (
    <div className="space-y-4">
      {missing.count > 0 && (
        <div className="bg-amber-50 border border-amber-300 rounded-lg shadow-sm p-4 flex items-center justify-between">
          <div>
            <p className="text-amber-800 font-medium">
              {missing.count} impresora{missing.count === 1 ? "" : "s"} activas no registradas en HP Web
              Jetadmin
            </p>
            <p className="text-amber-700 text-sm">
              Equipos con estatus activo que no aparecen en los reportes de HP Web Jetadmin.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setMissingOpen(true)}
            className="bg-amber-600 text-white text-sm px-4 py-2 rounded-md hover:bg-amber-700 shrink-0"
          >
            Ver detalle
          </button>
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-wrap gap-4 items-end">
          <FilterSelect
            label="Region"
            value={region}
            onChange={resetToFirstPage(setRegion)}
            options={filters.regions}
          />
          <FilterSelect
            label="Categoria"
            value={category}
            onChange={resetToFirstPage(setCategory)}
            options={filters.categories}
          />
          <FilterSelect
            label="Fecha"
            value={period}
            onChange={resetToFirstPage(setPeriod)}
            options={filters.periods}
          />
          <FilterSelect
            label="Status Impresora"
            value={printerStatus}
            onChange={resetToFirstPage(setPrinterStatus)}
            options={filters.printer_statuses}
          />
          <FilterSelect
            label="Oficina"
            value={office}
            onChange={resetToFirstPage(setOffice)}
            options={filters.offices}
          />
          <label className="flex flex-col gap-1 text-sm flex-1 min-w-[200px]">
            <span className="text-slate-500 text-xs uppercase tracking-wide">Buscar</span>
            <input
              type="text"
              placeholder="IP, nombre, serie, oficina..."
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
              className="border rounded-md px-3 py-1.5 text-sm"
            />
          </label>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-slate-800">Contadores mensuales</h2>
            <p className="text-sm text-slate-500">
              {data.count} registro{data.count === 1 ? "" : "s"}. Haz clic en una fila para ver el
              detalle completo.
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={handleExport}
              disabled={exporting}
              className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:bg-emerald-400"
            >
              {exporting ? "Exportando..." : "Exportar Excel"}
            </button>
            <div className="text-right">
              <p className="text-xs text-slate-500 uppercase tracking-wide">Total Contador Mensual</p>
              <p className="text-lg font-semibold text-slate-800">{formatNumber(totalMonthly)}</p>
            </div>
          </div>
        </div>

        {!loading && !chartLoading && periodData.length > 0 && (
          <div className="p-4 border-b">
            <h3 className="text-sm font-medium text-slate-700 mb-2">
              Contadores por mes
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={periodData} margin={{ top: 5, right: 5, left: -20, bottom: 30 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="period" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(v) => v.toLocaleString()} />
                  <Bar dataKey="total" fill="#0ea5e9" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
        {error && <p className="p-4 text-red-600">{error}</p>}
        {loading ? (
          <p className="p-4 text-slate-500">Cargando...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm table-fixed">
              <thead className="bg-slate-50 text-slate-600 text-left">
                <tr>
                  <SortHeader field="display_name">Nombre</SortHeader>
                  <SortHeader field="ip_address">IPv4Address</SortHeader>
                  <SortHeader field="serial_number">Serial</SortHeader>
                  <SortHeader field="region">Region</SortHeader>
                  <SortHeader field="category">Categoria</SortHeader>
                  <SortHeader field="office__name">Nombre Oficina</SortHeader>
                  <SortHeader field="office__status">Estatus Oficina</SortHeader>
                  <SortHeader field="period">Fecha</SortHeader>
                  <SortHeader field="monthly_counter" align="right">Contador Mensual</SortHeader>
                  <SortHeader field="printer_status">Status Impresora</SortHeader>
                </tr>
              </thead>
              <tbody>
                {data.results.map((entry) => (
                  <tr
                    key={entry.id}
                    onClick={() => setSelected(entry)}
                    className="border-t hover:bg-slate-50 cursor-pointer"
                    onMouseEnter={(e) =>
                      setTooltip({
                        visible: true,
                        text: entry.observations?.trim() || "Sin observaciones",
                        x: e.clientX,
                        y: e.clientY,
                      })
                    }
                    onMouseMove={(e) =>
                      setTooltip((t) => ({ ...t, x: e.clientX, y: e.clientY }))
                    }
                    onMouseLeave={() => setTooltip((t) => ({ ...t, visible: false }))}
                  >
                    <td className="px-2 py-1.5 truncate">{entry.impresora?.name || "-"}</td>
                    <td className="px-2 py-1.5 truncate font-mono">{entry.ip_address || "-"}</td>
                    <td className="px-2 py-1.5 truncate font-mono">{entry.impresora?.serial_number || "-"}</td>
                    <td className="px-2 py-1.5 truncate">{entry.region || "-"}</td>
                    <td className="px-2 py-1.5 truncate">{entry.category || "-"}</td>
                    <td className="px-2 py-1.5 truncate">{entry.office_name || "-"}</td>
                    <td className="px-2 py-1.5 truncate">{entry.office_status || "-"}</td>
                    <td className="px-2 py-1.5 truncate">{entry.period || "-"}</td>
                    <td className="px-2 py-1.5 text-right truncate">{formatNumber(entry.monthly_counter)}</td>
                    <td className="px-2 py-1.5 truncate">{entry.printer_status || "-"}</td>
                  </tr>
                ))}
                {data.results.length === 0 && (
                  <tr>
                    <td colSpan={10} className="px-4 py-3 text-center text-slate-500">
                      Sin resultados.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex items-center justify-between p-4 border-t text-sm">
          <button
            type="button"
            disabled={!data.previous}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="px-3 py-1.5 rounded-md bg-slate-100 text-slate-700 disabled:opacity-40 hover:bg-slate-200"
          >
            Anterior
          </button>
          <span className="text-slate-500">
            Pagina {page} de {totalPages}
          </span>
          <button
            type="button"
            disabled={!data.next}
            onClick={() => setPage((p) => p + 1)}
            className="px-3 py-1.5 rounded-md bg-slate-100 text-slate-700 disabled:opacity-40 hover:bg-slate-200"
          >
            Siguiente
          </button>
        </div>
      </div>

      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected?.impresora?.name || "Detalle"}
        subtitle={selected?.impresora?.ip_address}
      >
        {selected && form && (
          <CounterDetail
            entry={selected}
            form={form}
            editing={editing}
            saving={saving}
            saveError={saveError}
            isAdmin={isAdmin}
            onChange={handleFieldChange}
            onEdit={() => setEditing(true)}
            onCancel={handleCancelEdit}
            onSave={handleSave}
          />
        )}
      </Modal>

      <Modal
        open={missingOpen}
        onClose={() => setMissingOpen(false)}
        title="Impresoras sin lectura reciente"
        subtitle={`Ultimos ${missing.days} dias`}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm border">
            <thead className="bg-slate-50 text-slate-600 text-left">
              <tr>
                <th className="px-3 py-1.5">Nombre</th>
                <th className="px-3 py-1.5">IP</th>
                <th className="px-3 py-1.5">Oficina</th>
                <th className="px-3 py-1.5">Status</th>
                <th className="px-3 py-1.5">Ultima lectura</th>
                <th className="px-3 py-1.5">Ping</th>
              </tr>
            </thead>
            <tbody>
              {missing.results.map((m) => {
                const status = pingStatus[m.ip_address];
                return (
                  <tr key={m.monthly_counter_id} className="border-t">
                    <td className="px-3 py-1.5">{m.name || "-"}</td>
                    <td className="px-3 py-1.5 font-mono">{m.ip_address || "-"}</td>
                    <td className="px-3 py-1.5">{m.office_name || "-"}</td>
                    <td className="px-3 py-1.5">
                      <select
                        value={m.printer_status || ""}
                        disabled={!isAdmin || savingStatusId === m.impresora_id}
                        onChange={(e) => handleStatusChange(m.impresora_id, e.target.value)}
                        className="border rounded-md px-2 py-1 text-xs bg-white disabled:opacity-50"
                      >
                        {!allStatuses.includes(m.printer_status) && m.printer_status && (
                          <option value={m.printer_status}>{m.printer_status}</option>
                        )}
                        {allStatuses.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-3 py-1.5">
                      {m.last_captured_at ? new Date(m.last_captured_at).toLocaleString() : "Nunca"}
                    </td>
                    <td className="px-3 py-1.5">
                      {m.ip_address ? (
                        <button
                          type="button"
                          onClick={() => handlePing(m.ip_address)}
                          disabled={status === "loading"}
                          className="px-2 py-1 rounded-md text-xs bg-slate-100 hover:bg-slate-200 disabled:opacity-50"
                        >
                          {status === "loading" ? "Verificando..." : "Ping"}
                        </button>
                      ) : (
                        "-"
                      )}
                      {status === "up" && (
                        <span className="ml-2 text-xs text-emerald-600 font-medium">Responde</span>
                      )}
                      {status === "down" && (
                        <span className="ml-2 text-xs text-red-600 font-medium">No responde</span>
                      )}
                      {status === "error" && (
                        <span className="ml-2 text-xs text-red-600 font-medium">Error</span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {missing.results.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-3 py-3 text-center text-slate-500">
                    Sin resultados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Modal>

      {tooltip.visible &&
        createPortal(
          <div
            className="fixed z-50 max-w-xs rounded-md bg-slate-800 px-3 py-2 text-xs text-white shadow-lg"
            style={{
              left: tooltip.x,
              top: tooltip.y,
              transform: "translate(-50%, -110%)",
            }}
          >
            {tooltip.text}
          </div>,
          document.body
        )}
    </div>
  );
}

function DetailSection({ title, children }) {
  return (
    <div className="mb-4">
      <h4 className="text-xs uppercase tracking-wide text-slate-500 mb-2">{title}</h4>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">{children}</div>
    </div>
  );
}

function Field({ label, name, value, editing, onChange, type = "text" }) {
  if (editing) {
    return (
      <label className="block">
        <span className="text-xs text-slate-400">{label}</span>
        {type === "textarea" ? (
          <textarea
            value={value ?? ""}
            onChange={(e) => onChange(name, e.target.value)}
            rows={2}
            className="mt-0.5 w-full border rounded-md px-2 py-1 text-sm"
          />
        ) : (
          <input
            type={type}
            value={value ?? ""}
            onChange={(e) =>
              onChange(name, type === "number" ? (e.target.value === "" ? null : Number(e.target.value)) : e.target.value)
            }
            className="mt-0.5 w-full border rounded-md px-2 py-1 text-sm"
          />
        )}
      </label>
    );
  }
  return (
    <div>
      <p className="text-xs text-slate-400">{label}</p>
      <p className="text-sm text-slate-800">
        {value === "" || value === null || value === undefined
          ? "-"
          : type === "number"
          ? formatNumber(value)
          : value}
      </p>
    </div>
  );
}

function CounterTable({ form, editing, onChange }) {
  const weeks = [
    { label: "Semana 1", total: "week1_counter", final: "week1_final" },
    { label: "Semana 2", total: "week2_counter", final: "week2_final" },
    { label: "Semana 3", total: "week3_counter", final: "week3_final" },
    { label: "Semana 4", total: "week4_counter", final: "week4_final" },
    { label: "Semana 5", total: "week5_counter", final: "week5_final" },
  ];

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Field
          label="Contador del Mes Anterior"
          name="previous_month_counter"
          value={form.previous_month_counter}
          editing={editing}
          onChange={onChange}
          type="number"
        />
        <Field
          label="Contador Mensual"
          name="monthly_counter"
          value={form.monthly_counter}
          editing={editing}
          onChange={onChange}
          type="number"
        />
      </div>

      {weeks.map((w) => (
        <details key={w.label} className="border rounded-md">
          <summary className="px-3 py-2 text-sm font-medium text-slate-700 cursor-pointer hover:bg-slate-50">
            {w.label}
          </summary>
          <div className="p-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field
              label="Contador Total"
              name={w.total}
              value={form[w.total]}
              editing={editing}
              onChange={onChange}
              type="number"
            />
            <Field
              label="Contador Final"
              name={w.final}
              value={form[w.final]}
              editing={editing}
              onChange={onChange}
              type="number"
            />
          </div>
        </details>
      ))}
    </div>
  );
}

function CounterDetail({ entry, form, editing, saving, saveError, isAdmin, onChange, onEdit, onCancel, onSave }) {
  return (
    <div>
      {isAdmin ? (
        <div className="flex items-center justify-end gap-2 mb-3">
          {editing ? (
            <>
              <button
                type="button"
                onClick={onCancel}
                disabled={saving}
                className="px-3 py-1.5 rounded-md text-sm bg-slate-100 text-slate-700 hover:bg-slate-200 disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={onSave}
                disabled={saving}
                className="px-3 py-1.5 rounded-md text-sm bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? "Guardando..." : "Guardar"}
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={onEdit}
              className="px-3 py-1.5 rounded-md text-sm bg-slate-100 text-slate-700 hover:bg-slate-200"
            >
              Editar
            </button>
          )}
        </div>
      ) : (
        <p className="text-xs text-slate-500 text-right mb-3">Solo lectura</p>
      )}

      {saveError && <p className="text-sm text-red-600 mb-3">{saveError}</p>}

      <DetailSection title="Ubicacion">
        <Field label="Region" name="region" value={form.region} editing={editing} onChange={onChange} />
        <Field label="Categoria" name="category" value={form.category} editing={editing} onChange={onChange} />
        <Field label="Nombre Oficina" name="office_name" value={form.office_name} editing={editing} onChange={onChange} />
        <Field label="Piso" name="floor" value={form.floor} editing={editing} onChange={onChange} />
        <Field label="Nombre de Host Sede" name="host_name" value={form.host_name} editing={editing} onChange={onChange} />
        <Field label="Asignada o Ubicacion" name="location" value={form.location} editing={editing} onChange={onChange} />
      </DetailSection>

      <DetailSection title="Dispositivo">
        <Field label="DisplayName" value={form.impresora?.name} editing={false} onChange={() => {}} />
        <Field label="IPv4Address (del periodo)" value={form.ip_address} editing={false} onChange={() => {}} />
        <Field label="SerialNumber" value={form.impresora?.serial_number} editing={false} onChange={() => {}} />
        <Field label="Status Impresora (del periodo)" value={form.printer_status} editing={false} onChange={() => {}} />
      </DetailSection>

      <div className="mb-4">
        <h4 className="text-xs uppercase tracking-wide text-slate-500 mb-2">Contadores</h4>
        <CounterTable form={form} editing={editing} onChange={onChange} />
      </div>

      <DetailSection title="Periodo y notas">
        <Field label="Fecha" name="period" value={form.period} editing={editing} onChange={onChange} />
        <Field
          label="Observaciones"
          name="observations"
          value={form.observations}
          editing={editing}
          onChange={onChange}
          type="textarea"
        />
        <Field label="Archivo origen" value={entry.source_file} />
      </DetailSection>
    </div>
  );
}

export default Counters;
