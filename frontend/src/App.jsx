import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import Resume from './pages/Resume';
import Interviews from './pages/Interviews';
import MockSession from './pages/MockSession';
import StudyPlan from './pages/StudyPlan';

const Navigation = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="navbar">
      <div className="logo" style={{ cursor: 'pointer' }}>
        <Link to="/" style={{ color: 'inherit', display: 'flex', alignItems: 'center' }}>
          CareerAI
          <span className="logo-dot"></span>
        </Link>
      </div>

      <ul className="nav-links">
        {user ? (
          <>
            <li>
              <Link to="/dashboard" className={`nav-item ${isActive('/dashboard') ? 'active' : ''}`}>
                Dashboard
              </Link>
            </li>
            <li>
              <Link to="/resume" className={`nav-item ${isActive('/resume') ? 'active' : ''}`}>
                Resume
              </Link>
            </li>
            <li>
              <Link to="/interviews" className={`nav-item ${isActive('/interviews') ? 'active' : ''}`}>
                Interviews
              </Link>
            </li>
            <li>
              <Link to="/study-plan" className={`nav-item ${isActive('/study-plan') ? 'active' : ''}`}>
                Study Plan
              </Link>
            </li>
            <li>
              <div 
                className="user-menu" 
                onClick={() => navigate('/profile')}
                style={{ display: 'flex', alignItems: 'center' }}
              >
                <div className="avatar-circle">{user.name ? user.name[0] : 'U'}</div>
                <span className="user-name-label">{user.name}</span>
              </div>
            </li>
            <li>
              <button 
                onClick={logout} 
                className="logout-icon-btn" 
                style={{ background: 'none', border: 'none', font: 'inherit', display: 'flex', alignItems: 'center' }}
                title="Log Out"
              >
                <span style={{ fontSize: '1.2rem' }}>🚪</span>
              </button>
            </li>
          </>
        ) : (
          <>
            <li>
              <Link to="/login" className="nav-auth-btn nav-btn-login">
                Log In
              </Link>
            </li>
            <li>
              <Link to="/register" className="nav-auth-btn nav-btn-register">
                Register
              </Link>
            </li>
          </>
        )}
      </ul>
    </nav>
  );
};

const AppContent = () => {
  const { token } = useAuth();
  return (
    <div className="app-container">
      <Navigation />
      <Routes>
        <Route path="/login" element={!token ? <Login /> : <Navigate to="/dashboard" replace />} />
        <Route path="/register" element={!token ? <Register /> : <Navigate to="/dashboard" replace />} />
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/profile" 
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/resume" 
          element={
            <ProtectedRoute>
              <Resume />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/interviews" 
          element={
            <ProtectedRoute>
              <Interviews />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/interviews/session/:sessionId" 
          element={
            <ProtectedRoute>
              <MockSession />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/study-plan" 
          element={
            <ProtectedRoute>
              <StudyPlan />
            </ProtectedRoute>
          } 
        />
        <Route path="*" element={<Navigate to={token ? "/dashboard" : "/login"} replace />} />
      </Routes>
      <footer className="footer">
        © {new Date().getFullYear()} CareerAI. Elevating job readiness through artificial intelligence.
      </footer>
    </div>
  );
};

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;
