import { useState } from "react";
import Counters from './pages/Counters.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Catalogs from './pages/Catalogs.jsx'

const TABS = [
  { id: "counters", label: "Contadores mensuales", component: Counters },
  { id: "catalogs", label: "Catalogos", component: Catalogs },
  { id: "dashboard", label: "Consulta en HP Web Jetadmin", component: Dashboard },
];

function App() {
  const [tab, setTab] = useState("counters");
  const ActiveComponent = TABS.find((t) => t.id === tab)?.component ?? Counters;

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-slate-900 text-white shadow">
        <div className="w-full px-4 py-4">
          <h1 className="text-lg font-semibold">Impresoras</h1>
        </div>
      </header>

      <main className="w-full px-4 py-6">
        <div className="mb-4 flex gap-2 flex-wrap">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-md text-sm ${
                tab === t.id
                  ? "bg-slate-900 text-white"
                  : "bg-white text-slate-700 hover:bg-slate-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <ActiveComponent />
      </main>
    </div>
  )
}

export default App
