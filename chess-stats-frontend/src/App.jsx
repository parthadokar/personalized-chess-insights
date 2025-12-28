import { useState } from "react";
import { fetchUser, getAnalytics, getTopOpening, getMonthlyResults } from "./api";
import './index.css'
function App() {
  const [username, setUsername] = useState("");
  const [year, setYear] = useState("");
  const [month, setMonth] = useState("");
  const [loading, setLoading] = useState(false);

  const [userSaved, setUserSaved] = useState(null);
  const [analytics, setAnalyticsState] = useState(null);
  const [opening, setOpening] = useState(null);
  const [results, setResults] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);

      const res = await fetchUser(username, year, month);
      setUserSaved(res.data);

      const a = await getAnalytics(username);
      setAnalyticsState(a.data);

      const o = await getTopOpening(username);
      setOpening(o.data);

      const r = await getMonthlyResults(username, year, month);
      setResults(r.data);

    } catch (err) {
      alert(err.response?.data?.detail || "Error fetching data");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-10 flex justify-center">
      <div className="bg-white shadow p-6 w-full max-w-xl rounded">
        <h1 className="text-2xl font-bold mb-4">Chess Stats Dashboard</h1>

        {/* Input Form */}
        <div className="space-y-3">
          <input
            type="text"
            placeholder="Chess.com Username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            className="border p-2 w-full rounded"
          />
          <input
            type="number"
            placeholder="Year (e.g. 2024)"
            value={year}
            onChange={e => setYear(e.target.value)}
            className="border p-2 w-full rounded"
          />
          <input
            type="number"
            placeholder="Month (1-12)"
            value={month}
            onChange={e => setMonth(e.target.value)}
            className="border p-2 w-full rounded"
          />

          <button
            onClick={loadData}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded w-full"
          >
            {loading ? "Fetching…" : "Fetch & Analyze"}
          </button>
        </div>

        {/* Results */}
        {userSaved && (
          <div className="mt-6 p-4 bg-green-100 rounded">
            <p>Games saved this month: {userSaved.games_saved}</p>
          </div>
        )}

        {analytics && (
          <div className="mt-6">
            <h2 className="font-semibold text-lg">Player Analytics</h2>
            <p>Username: {analytics.username}</p>
            <p>Latest Blitz Rating: {analytics.latest_blitz || "None"}</p>
            <h3 className="mt-2 font-medium">Rating History:</h3>
            <ul className="list-disc ml-5">
              {analytics.all_ratings.map((r, i) => (
                <li key={i}>{r.mode}: {r.rating} ({r.date})</li>
              ))}
            </ul>
          </div>
        )}

        {opening && opening.top_opening && (
          <div className="mt-6">
            <h2 className="font-semibold text-lg">Top Opening</h2>
            <p>{opening.top_opening} ({opening.games_played} games)</p>
            <p>Wins: {opening.wins}, Losses: {opening.losses}, Draws: {opening.draws}</p>
            <p>Win Rate: {opening.win_rate}%</p>
          </div>
        )}

        {results && (
          <div className="mt-6 bg-gray-50 p-4 rounded">
            <h2 className="font-semibold">Monthly Results</h2>
            <p>Wins: {results.wins} | Losses: {results.losses}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
