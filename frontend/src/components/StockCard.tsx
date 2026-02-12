import { Link } from 'react-router-dom';
import ReadinessBadge from './ReadinessBadge';
import MosiScore from './MosiScore';

interface Props {
  stockId: number;
  symbol: string;
  name: string;
  status: string;
  mosiScore: number;
  modelType: string;
  sector?: string;
}

export default function StockCard({ stockId, symbol, name, status, mosiScore, modelType, sector }: Props) {
  return (
    <Link to={`/stock/${stockId}`} className="card" style={{ display: 'block', textDecoration: 'none', color: 'inherit' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontWeight: 600 }}>{symbol}</div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{name}</div>
          <div style={{ marginTop: 4, display: 'flex', gap: 6 }}>
            <ReadinessBadge status={status} />
            <span className="badge" style={{ background: '#e8eaf6', color: '#3f51b5' }}>{modelType}</span>
            {sector && <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{sector}</span>}
          </div>
        </div>
        <MosiScore score={mosiScore} />
      </div>
    </Link>
  );
}
