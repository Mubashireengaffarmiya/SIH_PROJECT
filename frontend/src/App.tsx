import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import NewInspection from './pages/NewInspection';
import AnalysisResult from './pages/AnalysisResult';
import History from './pages/History';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/inspect" element={<NewInspection />} />
          <Route path="/analysis/:id" element={<AnalysisResult />} />
          <Route path="/history" element={<History />} />
          <Route
            path="*"
            element={
              <div className="text-center pt-20">
                <p className="text-white text-xl font-bold">404 — Page not found</p>
              </div>
            }
          />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
