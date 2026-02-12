import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client';
import ReadinessBadge from '../components/ReadinessBadge';
import MosiScore from '../components/MosiScore';
import Disclaimer from '../components/Disclaimer';

const DETAIL_TABS = ['Summary', 'Layer 1', 'Layer 2', 'Layer 3'];

interface ReadinessDetail {
  stock_id: number;
  symbol: string;
  name: string;
  status: string;
  mosi_score: number;
  score_breakdown: {
    layer1_contribution: number;
    layer2_contribution: number;
    signal_contribution: number;
    total: number;
  };
  layer1_qualified: boolean;
  layer1_model: string;
  layer2_verdict: string | null;
}

interface AnalysisData {
  points: Array<{
    point_number: number;
    title: string;
    finding: string;
    score: number | null;
    evidence: string[];
  }>;
  multi_bagger_score: number;
  verdict: string;
  summary: string;
  documents_used: string[];
}

export default function StockDetail() {
  const { stockId } = useParams<{ stockId: string }>();
  const [activeTab, setActiveTab] = useState(0);
  const [readiness, setReadiness] = useState<ReadinessDetail | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!stockId) return;
    const id = parseInt(stockId);
    setLoading(true);
    Promise.all([
      api.getReadinessDetail(id).catch(() => null),
      api.getAnalysis(id).catch(() => null),
    ]).then(([r, a]) => {
      setReadiness(r as ReadinessDetail | null);
      setAnalysis(a as AnalysisData | null);
      setLoading(false);
    });
  }, [stockId]);

  if (loading) return <div className="loading">Loading...</div>;
  if (!readiness) return <div className="error">Stock not found</div>;

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <h1>{readiness.symbol}</h1>
        <div style={{ color: 'var(--text-secondary)' }}>{readiness.name}</div>
        <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
          <ReadinessBadge status={readiness.status} />
          <MosiScore score={readiness.mosi_score} />
        </div>
      </div>

      <div className="tabs">
        {DETAIL_TABS.map((tab, i) => (
          <div key={tab} className={`tab ${activeTab === i ? 'tab--active' : ''}`} onClick={() => setActiveTab(i)}>
            {tab}
          </div>
        ))}
      </div>

      {activeTab === 0 && <SummaryTab readiness={readiness} analysis={analysis} />}
      {activeTab === 1 && <Layer1Tab readiness={readiness} />}
      {activeTab === 2 && <Layer2Tab analysis={analysis} />}
      {activeTab === 3 && <Layer3Tab />}

      <Disclaimer />
    </div>
  );
}

function SummaryTab({ readiness, analysis }: { readiness: ReadinessDetail; analysis: AnalysisData | null }) {
  const breakdown = readiness.score_breakdown;
  return (
    <div>
      <div className="card">
        <h3>MOSI Score Breakdown</h3>
        <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
          <ScoreBar label="Layer 1" value={breakdown.layer1_contribution} max={33.3} />
          <ScoreBar label="Layer 2" value={breakdown.layer2_contribution} max={33.3} />
          <ScoreBar label="Signal" value={breakdown.signal_contribution} max={33.3} />
        </div>
      </div>
      {analysis && (
        <div className="card">
          <h3>AI Verdict: {analysis.verdict}</h3>
          <div style={{ color: 'var(--text-secondary)', marginTop: 4 }}>Multi-Bagger Score: {analysis.multi_bagger_score}/10</div>
          <p style={{ marginTop: 8 }}>{analysis.summary}</p>
        </div>
      )}
    </div>
  );
}

function ScoreBar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{label}</div>
      <div style={{ height: 8, background: '#e0e0e0', borderRadius: 4, marginTop: 4 }}>
        <div style={{ height: '100%', width: `${pct}%`, background: 'var(--primary)', borderRadius: 4 }} />
      </div>
      <div style={{ fontSize: 12, marginTop: 2 }}>{value.toFixed(1)}</div>
    </div>
  );
}

function Layer1Tab({ readiness }: { readiness: ReadinessDetail }) {
  return (
    <div className="card">
      <h3>Layer 1 — Screener</h3>
      <div style={{ marginTop: 8 }}>
        <div>Qualified: {readiness.layer1_qualified ? 'Yes' : 'No'}</div>
        <div>Model: {readiness.layer1_model}</div>
      </div>
    </div>
  );
}

function Layer2Tab({ analysis }: { analysis: AnalysisData | null }) {
  if (!analysis) return <div className="empty">Layer 2 analysis not available</div>;

  return (
    <div>
      <div className="card" style={{ marginBottom: 8 }}>
        <h3>11-Point AI Analysis</h3>
        <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
          Verdict: {analysis.verdict} | Multi-Bagger Score: {analysis.multi_bagger_score}/10
        </div>
      </div>
      {analysis.points.map((pt) => (
        <details key={pt.point_number} className="card" style={{ cursor: 'pointer' }}>
          <summary style={{ fontWeight: 500 }}>
            {pt.point_number}. {pt.title}
            {pt.score !== null && <span style={{ float: 'right', color: 'var(--text-secondary)' }}>{pt.score}/10</span>}
          </summary>
          <p style={{ marginTop: 8 }}>{pt.finding}</p>
          {pt.evidence.length > 0 && (
            <div style={{ marginTop: 4, fontSize: 12, color: 'var(--text-secondary)' }}>
              Evidence: {pt.evidence.join(', ')}
            </div>
          )}
        </details>
      ))}
    </div>
  );
}

function Layer3Tab() {
  return (
    <div className="card">
      <h3>Layer 3 — Technical Signals</h3>
      <div style={{ color: 'var(--text-secondary)', marginTop: 8 }}>
        Technical indicator chart and signal status will be displayed here when connected to live data feed.
      </div>
    </div>
  );
}
