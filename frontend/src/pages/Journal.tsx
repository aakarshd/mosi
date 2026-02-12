import { useState, useEffect } from 'react';
import { api } from '../api/client';

interface JournalEntry {
  id: number;
  symbol: string;
  name: string;
  trade_type: string;
  quantity: number;
  price: number;
  trade_date: string;
  auto_logged: boolean;
  mosi_context: Record<string, unknown> | null;
  notes: string | null;
}

interface BehavioralReport {
  month_label: string;
  discipline_score: number;
  patterns: Record<string, unknown>;
  insights: string;
}

export default function Journal() {
  const [activeTab, setActiveTab] = useState(0);
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [report, setReport] = useState<BehavioralReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (activeTab === 0) {
      setLoading(true);
      api.getJournalEntries()
        .then((data) => setEntries((data as { data: JournalEntry[] }).data))
        .catch(() => setEntries([]))
        .finally(() => setLoading(false));
    } else {
      setLoading(true);
      api.getBehavioralReport()
        .then((data) => setReport(data as BehavioralReport))
        .catch(() => setReport(null))
        .finally(() => setLoading(false));
    }
  }, [activeTab]);

  return (
    <div>
      <h1 style={{ marginBottom: 16 }}>Journal</h1>

      <div className="tabs">
        <div className={`tab ${activeTab === 0 ? 'tab--active' : ''}`} onClick={() => setActiveTab(0)}>
          Trade Log
        </div>
        <div className={`tab ${activeTab === 1 ? 'tab--active' : ''}`} onClick={() => setActiveTab(1)}>
          Behavioral Report
        </div>
      </div>

      {loading && <div className="loading">Loading...</div>}

      {!loading && activeTab === 0 && (
        <>
          {entries.length === 0 && <div className="empty">No trade entries yet</div>}
          {entries.map((e) => (
            <div key={e.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div>
                  <span style={{ fontWeight: 600 }}>{e.symbol}</span>
                  <span style={{ marginLeft: 8, fontSize: 12, textTransform: 'uppercase',
                    color: e.trade_type === 'buy' ? 'var(--success)' : e.trade_type === 'sell' ? 'var(--danger)' : 'var(--warning)' }}>
                    {e.trade_type}
                  </span>
                </div>
                <div style={{ textAlign: 'right', fontSize: 13 }}>
                  <div>{e.quantity} @ {e.price}</div>
                  <div style={{ color: 'var(--text-secondary)' }}>{e.trade_date}</div>
                </div>
              </div>
              {e.auto_logged && <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>Auto-logged from broker</div>}
              {e.notes && <div style={{ marginTop: 4, fontSize: 13 }}>{e.notes}</div>}
              {e.mosi_context && (
                <div style={{ marginTop: 4, fontSize: 12, color: 'var(--text-secondary)' }}>
                  MOSI Context: {JSON.stringify(e.mosi_context).substring(0, 100)}...
                </div>
              )}
            </div>
          ))}
        </>
      )}

      {!loading && activeTab === 1 && (
        <>
          {!report && <div className="empty">No behavioral report available</div>}
          {report && (
            <div>
              <div className="card">
                <h3>Behavioral Report — {report.month_label}</h3>
                <div style={{ marginTop: 8 }}>
                  <div>Value Discipline Score: <strong>{report.discipline_score}%</strong></div>
                </div>
              </div>
              <div className="card">
                <h3>Insights</h3>
                <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, marginTop: 8 }}>{report.insights}</pre>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
