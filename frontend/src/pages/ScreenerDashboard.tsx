import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import StockCard from '../components/StockCard';
import Disclaimer from '../components/Disclaimer';

const TABS = [
  { key: 'ready_now', label: 'Ready Now' },
  { key: 'getting_ready', label: 'Getting Ready' },
  { key: 'not_ready', label: 'Not Ready' },
  { key: 'exit_alert', label: 'Exit Alert' },
];

interface ReadinessItem {
  stock_id: number;
  symbol: string;
  name: string;
  status: string;
  mosi_score: number;
  layer1_model: string;
}

export default function ScreenerDashboard() {
  const [activeTab, setActiveTab] = useState('ready_now');
  const [stocks, setStocks] = useState<ReadinessItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [counts, setCounts] = useState<Record<string, number>>({});

  const fetchStocks = useCallback(async (status: string) => {
    setLoading(true);
    setError('');
    try {
      const result = await api.getReadinessList(status) as { data: ReadinessItem[]; pagination: { total: number } };
      setStocks(result.data);
      setCounts((prev) => ({ ...prev, [status]: result.pagination.total }));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStocks(activeTab);
  }, [activeTab, fetchStocks]);

  return (
    <div>
      <h1 style={{ marginBottom: 16 }}>Screener Dashboard</h1>

      <div className="tabs">
        {TABS.map((tab) => (
          <div
            key={tab.key}
            className={`tab ${activeTab === tab.key ? 'tab--active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
            {counts[tab.key] !== undefined && (
              <span style={{ marginLeft: 4, fontSize: 12, opacity: 0.7 }}>({counts[tab.key]})</span>
            )}
          </div>
        ))}
      </div>

      {loading && <div className="loading">Loading...</div>}
      {error && <div className="error">{error}</div>}

      {!loading && !error && stocks.length === 0 && (
        <div className="empty">No stocks in this category</div>
      )}

      {!loading && !error && stocks.map((stock) => (
        <StockCard
          key={stock.stock_id}
          stockId={stock.stock_id}
          symbol={stock.symbol}
          name={stock.name}
          status={stock.status}
          mosiScore={stock.mosi_score}
          modelType={stock.layer1_model}
        />
      ))}

      <Disclaimer />
    </div>
  );
}
