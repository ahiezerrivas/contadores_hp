import { useEffect, useState } from "react";
import {
  getImpresoras,
  getOficinas,
  updateImpresora,
  updateOficina,
} from "../api/client";
import Modal from "../components/Modal.jsx";

const OFICINA_FIELDS = [
  { key: "name", label: "Nombre", type: "text" },
  { key: "status", label: "Estatus", type: "select", options: ["Activo", "Inactivo"], default: "Activo" },
  { key: "region", label: "Region", type: "text" },
  { key: "code", label: "Codigo", type: "text" },
];

const IMPRESORA_FIELDS = [
  { key: "name", label: "Nombre", type: "text" },
  { key: "model_name", label: "Modelo", type: "text" },
  { key: "ip_address", label: "IP", type: "text" },
  { key: "serial_number", label: "Serial", type: "text" },
  { key: "status", label: "Status", type: "text" },
];

function FieldsForm({ fields, form, onChange }) {
  return (
    <div className="grid grid-cols-1 gap-3">
      {fields.map((f) => (
        <label key={f.key} className="flex flex-col gap-1 text-sm">
          <span className="text-slate-500 text-xs uppercase tracking-wide">{f.label}</span>
          {f.type === "select" ? (
            <select
              value={form[f.key]}
              onChange={(e) => onChange(f.key, e.target.value)}
              className="border rounded-md px-3 py-1.5 text-sm bg-white"
            >
              {f.options.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              value={form[f.key]}
              onChange={(e) => onChange(f.key, e.target.value)}
              className="border rounded-md px-3 py-1.5 text-sm"
            />
          )}
        </label>
      ))}
    </div>
  );
}

function CatalogPanel({ title, fields, api }) {
  const [data, setData] = useState({ count: 0, next: null, previous: null, results: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [editingItem, setEditingItem] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [saving, setSaving] = useState(false);

  const fetch = () => {
    setLoading(true);
    setError(null);
    const params = { page };
    if (search.trim()) params.search = search.trim();
    api
      .get(params)
      .then(setData)
      .catch(() => setError(`No se pudieron cargar ${title.toLowerCase()}.`))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, search]);

  const startEdit = (item) => {
    setEditForm(Object.fromEntries(fields.map((f) => [f.key, item[f.key] ?? ""])));
    setEditingItem(item);
  };

  const handleUpdate = () => {
    setSaving(true);
    setError(null);
    api
      .update(editingItem.id, editForm)
      .then(() => {
        setEditingItem(null);
        fetch();
      })
      .catch(() => setError("No se pudo guardar el registro."))
      .finally(() => setSaving(false));
  };

  const onSearch = (value) => {
    setSearch(value);
    setPage(1);
  };

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg shadow p-4 space-y-3">
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Buscar..."
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            className="border rounded-md px-3 py-1.5 text-sm w-full max-w-xs"
          />
          {error && <span className="text-red-600 text-sm">{error}</span>}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-100 text-slate-600">
              <tr>
                {fields.map((f) => (
                  <th key={f.key} className="px-4 py-2">
                    {f.label}
                  </th>
                ))}
                <th className="px-4 py-2 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={fields.length + 1} className="px-4 py-4 text-slate-500">
                    Cargando...
                  </td>
                </tr>
              ) : data.results.length === 0 ? (
                <tr>
                  <td colSpan={fields.length + 1} className="px-4 py-4 text-slate-500">
                    No hay registros.
                  </td>
                </tr>
              ) : (
                data.results.map((item) => (
                  <tr key={item.id} className="border-b hover:bg-slate-50">
                    {fields.map((f) => (
                      <td key={f.key} className="px-4 py-2">
                        {item[f.key] ?? "-"}
                      </td>
                    ))}
                    <td className="px-4 py-2 text-right">
                      <button
                        type="button"
                        onClick={() => startEdit(item)}
                        className="text-slate-600 hover:text-slate-900"
                      >
                        Editar
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="flex justify-between items-center text-sm text-slate-600">
          <span>
            {data.count} registro{data.count === 1 ? "" : "s"}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => p - 1)}
              disabled={!data.previous}
              className="px-3 py-1 border rounded-md hover:bg-slate-100 disabled:opacity-50"
            >
              Anterior
            </button>
            <button
              type="button"
              onClick={() => setPage((p) => p + 1)}
              disabled={!data.next}
              className="px-3 py-1 border rounded-md hover:bg-slate-100 disabled:opacity-50"
            >
              Siguiente
            </button>
          </div>
        </div>
      </div>

      <Modal
        open={!!editingItem}
        onClose={() => setEditingItem(null)}
        title={`Editar ${title.toLowerCase()}`}
        subtitle={editingItem ? `ID: ${editingItem.id}` : ""}
      >
        <div className="space-y-4">
          <FieldsForm
            fields={fields}
            form={editForm}
            onChange={(key, value) => setEditForm((s) => ({ ...s, [key]: value }))}
          />
          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={() => setEditingItem(null)}
              className="bg-white text-slate-700 border text-sm px-4 py-2 rounded-md hover:bg-slate-100"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleUpdate}
              disabled={saving}
              className="bg-slate-900 text-white text-sm px-4 py-2 rounded-md hover:bg-slate-800 disabled:opacity-50"
            >
              Guardar
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

function Catalogs() {
  const [tab, setTab] = useState("oficinas");

  const tabs = [
    {
      id: "oficinas",
      label: "Oficinas",
      fields: OFICINA_FIELDS,
      api: {
        get: getOficinas,
        update: updateOficina,
      },
    },
    {
      id: "impresoras",
      label: "Impresoras",
      fields: IMPRESORA_FIELDS,
      api: {
        get: getImpresoras,
        update: updateImpresora,
      },
    },
  ];

  const active = tabs.find((t) => t.id === tab);

  return (
    <div className="space-y-4">
      <div className="flex gap-2 flex-wrap">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-md text-sm ${
              tab === t.id ? "bg-slate-900 text-white" : "bg-white text-slate-700 hover:bg-slate-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <CatalogPanel
        key={active.id}
        title={active.label}
        fields={active.fields}
        api={active.api}
      />
    </div>
  );
}

export default Catalogs;
