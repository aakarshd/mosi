import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import ScreenerDashboard from './pages/ScreenerDashboard';
import StockDetail from './pages/StockDetail';
import Portfolio from './pages/Portfolio';
import Journal from './pages/Journal';
import Settings from './pages/Settings';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/screener" replace />} />
        <Route path="/screener" element={<ScreenerDashboard />} />
        <Route path="/stock/:stockId" element={<StockDetail />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/journal" element={<Journal />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  );
}
