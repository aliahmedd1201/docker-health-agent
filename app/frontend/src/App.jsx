import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState("checking");
  const [refreshKey, setRefreshKey] = useState(0);

  // Fetch items from the backend on load and whenever Refresh is clicked
  useEffect(() => {
    async function load() {
      try {
        const res = await fetch("/api/items");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setItems(await res.json());
        setStatus("online");
      } catch {
        setItems([]);
        setStatus("offline");
      }
    }
    load();
  }, [refreshKey]);

  function refresh() {
    setStatus("checking");
    setRefreshKey((k) => k + 1);
  }

  return (
    <main className="container">
      <h1>Docker Health Agent</h1>
      <p className={`status ${status}`}>Backend: {status}</p>
      <button onClick={refresh}>Refresh</button>
      <ul>
        {items.map((item) => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </main>
  );
}

export default App;