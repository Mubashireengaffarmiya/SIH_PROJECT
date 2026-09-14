import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import NewInspection from './pages/NewInspection';
import AnalysisResult from './pages/AnalysisResult';
import History from './pages/History';
import ReviewQueue from './pages/ReviewQueue';
import AdminPages from './pages/AdminPages';

function PrivateRoute({ children, allowedRoles }: { children: React.ReactNode, allowedRoles?: string[] }) {
  const { isAuthenticated, user } = useAuth();
  
  if (!isAuthenticated) return <Navigate to="/login" />;
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" />; // Redirect to their default dashboard if unauthorized
  }
  
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/" element={<Navigate to="/dashboard" />} />
          
          <Route path="/dashboard" element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          } />
          
          <Route path="/inspect" element={
            <PrivateRoute allowedRoles={['INSPECTOR', 'ADMIN']}>
              <NewInspection />
            </PrivateRoute>
          } />
          
          <Route path="/analysis/:id" element={
            <PrivateRoute>
              <AnalysisResult />
            </PrivateRoute>
          } />
          
          <Route path="/history" element={
            <PrivateRoute>
              <History />
            </PrivateRoute>
          } />

          <Route path="/review-queue" element={
            <PrivateRoute allowedRoles={['REVIEWER', 'ADMIN']}>
              <ReviewQueue />
            </PrivateRoute>
          } />

          <Route path="/admin/*" element={
            <PrivateRoute allowedRoles={['ADMIN']}>
              <AdminPages />
            </PrivateRoute>
          } />
          
          <Route
            path="*"
            element={
              <div className="text-center pt-20">
                <p className="text-white text-xl font-bold">404 — Page not found</p>
              </div>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
