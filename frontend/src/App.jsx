import { useEffect, useMemo, useState } from "react";
import Counters from './pages/Counters.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Catalogs from './pages/Catalogs.jsx'
import Login from './pages/Login.jsx'
import { me } from './api/client.js'

const ALL_TABS = [
  { id: "counters", label: "Contadores mensuales", component: Counters, guest: true },
  { id: "dashboard", label: "Consulta en HP Web Jetadmin", component: Dashboard, guest: true },
  { id: "catalogs", label: "Catalogos", component: Catalogs, guest: false },
];

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("counters");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }
    me()
      .then((data) => setUser(data))
      .catch(() => {
        localStorage.removeItem("token");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleLogin = (data) => {
    setUser(data);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  const tabs = useMemo(
    () => ALL_TABS.filter((t) => user?.is_admin || t.guest),
    [user]
  );

  const ActiveComponent = useMemo(() => {
    return tabs.find((t) => t.id === tab)?.component ?? Counters;
  }, [tabs, tab]);

  const isAdmin = user?.is_admin;

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center text-slate-600">
        Cargando...
      </div>
    );
  }

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-slate-900 text-white shadow">
        <div className="w-full px-4 py-4 flex items-center justify-between">
          <h1 className="text-lg font-semibold">Impresoras</h1>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-slate-300">
              {user.username} · {user.is_admin ? "Administrador" : "Invitado"}
            </span>
            <button
              onClick={handleLogout}
              className="rounded-md bg-slate-700 px-3 py-1.5 hover:bg-slate-600"
            >
              Salir
            </button>
          </div>
        </div>
      </header>

      <main className="w-full px-4 py-6">
        <div className="mb-4 flex gap-2 flex-wrap">
          {tabs.map((t) => (
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
        <ActiveComponent isAdmin={isAdmin} />
      </main>
    </div>
  );
}

export default App
