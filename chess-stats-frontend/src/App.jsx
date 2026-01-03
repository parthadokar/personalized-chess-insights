import { useState } from "react";
import axios from "axios";
import "./index.css";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

function App() {
  const [username, setUsername] = useState("");
  const [year, setYear] = useState("");
  const [month, setMonth] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await API.get(
        `/analytics/${username}/${year}/${month}/summary`
      );
      setData(res.data);
    } catch {
      alert("Error fetching data");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="container">

        <header className="card">
          <h1>Chess Analytics Dashboard</h1>
          <p className="subtitle">
            Monthly performance overview from Chess.com
          </p>
        </header>

        <section className="card">
          <input
            placeholder="Chess.com Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />

          <div className="row">
            <input
              placeholder="Year"
              value={year}
              onChange={(e) => setYear(e.target.value)}
            />
            <input
              placeholder="Month"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
            />
          </div>

          <button onClick={loadData} disabled={loading}>
            {loading ? "Analyzing…" : "Analyze Games"}
          </button>
        </section>

        {data && (
          <>
            <section className="stats">
              <div className="stat">
                <span>Games</span>
                <strong>{data.games}</strong>
              </div>
              <div className="stat">
                <span>Wins</span>
                <strong className="green">{data.wins}</strong>
              </div>
              <div className="stat">
                <span>Losses</span>
                <strong className="red">{data.losses}</strong>
              </div>
            </section>

            <section className="card">
              <h2>Latest Ratings</h2>
              <ul>
                {Object.entries(data.latest_ratings).map(([mode, rating]) => (
                  <li key={mode}>
                    <span>{mode}</span>
                    <strong>{rating}</strong>
                  </li>
                ))}
              </ul>
            </section>

            <section className="card">
              <h2>Top Openings</h2>
              <div className="openings">
                {data.top_openings.map((o, i) => (
                  <div key={i} className="opening">
                    <div>
                      <strong>{i + 1}. {o.opening}</strong>
                      <span>{o.games} games</span>
                    </div>
                    <div className="right">
                      <strong>{o.win_rate}%</strong>
                      <span>Win rate</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="card center">
              <span>Average Time per Move</span>
              <strong>{data.avg_move_time ?? "N/A"} seconds</strong>
            </section>
          </>
        )}

      </div>
    </div>
  );
}

export default App;
