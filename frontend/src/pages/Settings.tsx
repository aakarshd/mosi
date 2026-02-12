import { useState, useEffect } from 'react';
import { api } from '../api/client';

const ENTRY_RULES = [
  { value: 'breakout_volume_macd', label: 'Breakout + Volume + MACD', desc: 'All three conditions must align — most conservative entry.' },
  { value: 'macd_consolidation_volume', label: 'MACD + Consolidation + Volume', desc: 'MACD crossover during consolidation with volume surge.' },
  { value: 'breakout_volume', label: 'Breakout + Volume', desc: 'Price breaks resistance with volume confirmation.' },
];

const EXIT_RULES = [
  { value: 'eight_pct_drop', label: '8% Drop from Top', desc: 'Trailing stop — exit when price drops 8% from post-entry high.' },
  { value: 'macd_red', label: 'MACD Turning Red', desc: 'Exit on bearish MACD crossover.' },
  { value: 'trendline_breach', label: 'Support Trendline Breach', desc: 'Exit when price falls below the support trendline.' },
];

const ADDITION_CAPS = [
  { value: 'max_5_pct', label: 'Max 5%', desc: 'Conservative — max 5% of portfolio in one stock.' },
  { value: 'max_10_pct', label: 'Max 10%', desc: 'Moderate — max 10% of portfolio in one stock.' },
  { value: 'max_12_pct', label: 'Max 12%', desc: 'Aggressive — max 12% of portfolio in one stock.' },
];

const SIGNAL_SOURCES = [
  { value: 'layer3', label: 'Layer 3 Technical Rules', desc: 'Use MACD, breakout, and trendline indicators.' },
  { value: 'aarna', label: 'Aarna', desc: 'Use Aarna AI signals as alternative to technical rules.' },
];

interface TradingRules {
  entry_rule: string;
  addition_cap: string;
  exit_rule: string;
  signal_source: string;
}

export default function Settings() {
  const [rules, setRules] = useState<TradingRules>({
    entry_rule: 'breakout_volume_macd',
    addition_cap: 'max_5_pct',
    exit_rule: 'eight_pct_drop',
    signal_source: 'layer3',
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.getTradingRules()
      .then((data) => setRules(data as TradingRules))
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await api.updateTradingRules(rules);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // Error handling
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <h1 style={{ marginBottom: 16 }}>Settings</h1>

      <div className="card">
        <h3>Entry Rule</h3>
        {ENTRY_RULES.map((r) => (
          <label key={r.value} style={{ display: 'block', padding: '8px 0', cursor: 'pointer' }}>
            <input
              type="radio" name="entry" value={r.value}
              checked={rules.entry_rule === r.value}
              onChange={() => setRules({ ...rules, entry_rule: r.value })}
            />
            <span style={{ marginLeft: 8, fontWeight: 500 }}>{r.label}</span>
            <div style={{ marginLeft: 24, fontSize: 13, color: 'var(--text-secondary)' }}>{r.desc}</div>
          </label>
        ))}
      </div>

      <div className="card">
        <h3>Exit Rule</h3>
        {EXIT_RULES.map((r) => (
          <label key={r.value} style={{ display: 'block', padding: '8px 0', cursor: 'pointer' }}>
            <input
              type="radio" name="exit" value={r.value}
              checked={rules.exit_rule === r.value}
              onChange={() => setRules({ ...rules, exit_rule: r.value })}
            />
            <span style={{ marginLeft: 8, fontWeight: 500 }}>{r.label}</span>
            <div style={{ marginLeft: 24, fontSize: 13, color: 'var(--text-secondary)' }}>{r.desc}</div>
          </label>
        ))}
      </div>

      <div className="card">
        <h3>Addition Cap</h3>
        {ADDITION_CAPS.map((r) => (
          <label key={r.value} style={{ display: 'block', padding: '8px 0', cursor: 'pointer' }}>
            <input
              type="radio" name="cap" value={r.value}
              checked={rules.addition_cap === r.value}
              onChange={() => setRules({ ...rules, addition_cap: r.value })}
            />
            <span style={{ marginLeft: 8, fontWeight: 500 }}>{r.label}</span>
            <div style={{ marginLeft: 24, fontSize: 13, color: 'var(--text-secondary)' }}>{r.desc}</div>
          </label>
        ))}
      </div>

      <div className="card">
        <h3>Signal Source</h3>
        {SIGNAL_SOURCES.map((r) => (
          <label key={r.value} style={{ display: 'block', padding: '8px 0', cursor: 'pointer' }}>
            <input
              type="radio" name="signal" value={r.value}
              checked={rules.signal_source === r.value}
              onChange={() => setRules({ ...rules, signal_source: r.value })}
            />
            <span style={{ marginLeft: 8, fontWeight: 500 }}>{r.label}</span>
            <div style={{ marginLeft: 24, fontSize: 13, color: 'var(--text-secondary)' }}>{r.desc}</div>
          </label>
        ))}
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        style={{
          background: 'var(--primary)', color: 'white', border: 'none', borderRadius: 'var(--radius)',
          padding: '10px 24px', fontSize: 14, cursor: saving ? 'not-allowed' : 'pointer', marginTop: 8,
        }}
      >
        {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Rules'}
      </button>
    </div>
  );
}
