import { useState, useEffect } from 'react';
import { api } from '../api/client';
import ReadinessBadge from '../components/ReadinessBadge';
import MosiScore from '../components/MosiScore';
import Disclaimer from '../components/Disclaimer';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

const COLORS = ['#1a73e8', '#34a853', '#fbbc04', '#ea4335', '#9c27b0', '#00bcd4'];

interface Holding {
  stock_id: number;
  symbol: string;
  name: string;
  mosi_score: number | null;
  compliance_status: string;
  deviation_reasons: string[];
}

interface Metrics {
  weighted_mosi_score: number;
  compliance_rate: number;
  total_holdings: number;
  sector_allocation: Array<{ label: string; percentage: number; value: number }>;
  model_allocation: Array<{ label: string; percentage: number; value: number }>;
}

export default function Portfolio() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getPortfolio()
      .then((data) => {
        const d = data as { holdings: Holding[]; metrics: Metrics };
        setHoldings(d.holdings);
        setMetrics(d.metrics);
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div>
      <h1 style={{ marginBottom: 16 }}>Portfolio</h1>

      {metrics && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: 16 }}>
          <div className="card">
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Avg MOSI Score</div>
            <MosiScore score={metrics.weighted_mosi_score} />
          </div>
          <div className="card">
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Compliance Rate</div>
            <div className="score">{metrics.compliance_rate.toFixed(0)}%</div>
          </div>
          <div className="card">
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Total Holdings</div>
            <div className="score">{metrics.total_holdings}</div>
          </div>
        </div>
      )}

      {metrics && metrics.sector_allocation.length > 0 && (
        <div className="card">
          <h3>Sector Allocation</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={metrics.sector_allocation}
                dataKey="percentage"
                nameKey="label"
                cx="50%" cy="50%"
                outerRadius={80}
              >
                {metrics.sector_allocation.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      <h2 style={{ marginBottom: 8 }}>Holdings</h2>
      {holdings.length === 0 && <div className="empty">No holdings to display</div>}
      {holdings.map((h) => (
        <div key={h.stock_id} className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontWeight: 600 }}>{h.symbol}</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{h.name}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              {h.mosi_score !== null && <MosiScore score={h.mosi_score} />}
              <div>
                <ReadinessBadge status={h.compliance_status === 'following_rules' ? 'ready_now' : 'exit_alert'} />
              </div>
            </div>
          </div>
          {h.deviation_reasons.length > 0 && (
            <div style={{ marginTop: 8, fontSize: 13, color: 'var(--danger)' }}>
              {h.deviation_reasons.map((r, i) => <div key={i}>{r}</div>)}
            </div>
          )}
        </div>
      ))}

      <Disclaimer />
    </div>
  );
}
