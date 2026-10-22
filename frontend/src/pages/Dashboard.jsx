import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';

import { API_URL } from '../config';

const Dashboard = () => {
  const { token, user } = useAuth();
  const navigate = useNavigate();

  // Dashboard state variables
  const [metrics, setMetrics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        setMetrics(data);
      } else {
        setError(data.detail || 'Failed to fetch dashboard metrics.');
      }
    } catch (err) {
      console.error(err);
      setError('Connection to backend failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score === null || score === undefined) return 'var(--text-muted)';
    if (score >= 75) return 'var(--success)';
    if (score >= 55) return 'var(--warning)';
    return 'var(--error)';
  };

  if (isLoading) {
    return (
      <div className="dashboard-container" style={{ alignSelf: 'flex-start', margin: '3rem auto' }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '350px' }}>
          <div className="spinner" style={{ width: '45px', height: '45px', borderThickness: '4px', marginBottom: '1.25rem' }}></div>
          <p style={{ color: 'var(--text-secondary)' }}>Loading analytics dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container" style={{ alignSelf: 'flex-start', margin: '2rem auto', maxWidth: '1200px', width: '95%' }}>
      
      {/* Header */}
      <div className="page-header" style={{ marginBottom: '1.5rem' }}>
        <h1 className="page-title">Dashboard & Analytics</h1>
        <p className="page-subtitle">
          Welcome back, <span style={{ color: 'var(--accent-color)', fontWeight: '700' }}>{user?.name}</span>. Trace your career preparation progress.
        </p>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {metrics && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {/* Headline Summary Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
            
            {/* ATS Score Card */}
            <div 
              className="card" 
              onClick={() => navigate('/resume')}
              style={{ cursor: 'pointer', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', background: 'rgba(99, 102, 241, 0.04)', borderColor: 'rgba(99, 102, 241, 0.15)' }}
            >
              <span style={{ fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Latest ATS Score</span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                <span style={{ fontSize: '2.25rem', fontWeight: '800', color: getScoreColor(metrics.latest_ats_score) }}>
                  {metrics.latest_ats_score !== null ? `${metrics.latest_ats_score}` : 'N/A'}
                </span>
                {metrics.latest_ats_score !== null && <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>/ 100</span>}
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Resume formatting optimization check</span>
            </div>

            {/* JD Match Card */}
            <div 
              className="card" 
              onClick={() => navigate('/resume')}
              style={{ cursor: 'pointer', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', background: 'rgba(168, 85, 247, 0.04)', borderColor: 'rgba(168, 85, 247, 0.15)' }}
            >
              <span style={{ fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Latest JD Match</span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                <span style={{ fontSize: '2.25rem', fontWeight: '800', color: getScoreColor(metrics.latest_match_score) }}>
                  {metrics.latest_match_score !== null ? `${metrics.latest_match_score}%` : 'N/A'}
                </span>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Resume similarity to target JDs</span>
            </div>

            {/* Avg Interview Rating Card */}
            <div 
              className="card" 
              onClick={() => navigate('/interviews')}
              style={{ cursor: 'pointer', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', background: 'rgba(16, 185, 129, 0.04)', borderColor: 'rgba(16, 185, 129, 0.15)' }}
            >
              <span style={{ fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Avg Interview Score</span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                <span style={{ fontSize: '2.25rem', fontWeight: '800', color: getScoreColor(metrics.avg_interview_score) }}>
                  {metrics.avg_interview_score !== null ? `${metrics.avg_interview_score}%` : 'N/A'}
                </span>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Rolling overall mock evaluation score</span>
            </div>

            {/* Questions Attempted Card */}
            <div 
              className="card" 
              onClick={() => navigate('/interviews')}
              style={{ cursor: 'pointer', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', background: 'rgba(255,255,255,0.015)' }}
            >
              <span style={{ fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Mock Answers Submitted</span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                <span style={{ fontSize: '2.25rem', fontWeight: '800', color: 'white' }}>
                  {metrics.questions_attempted}
                </span>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total prep questions attempted</span>
            </div>

          </div>

          {/* Visualizations Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '1.5rem' }}>
            
            {/* Line Chart: Interview Scores Over Time */}
            <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: '700', color: 'white' }}>Interview Score Progression</h3>
              
              {metrics.score_history.length === 0 ? (
                <div style={{ height: '260px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px dashed var(--border-color)', borderRadius: '8px' }}>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Complete mock sessions to view performance trends.</p>
                </div>
              ) : (
                <div style={{ height: '260px', width: '100%' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={metrics.score_history} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                      <CartesianGrid stroke="rgba(255,255,255,0.02)" strokeDasharray="3 3" />
                      <XAxis dataKey="idx" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                      <YAxis domain={[0, 100]} stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                      <Tooltip 
                        contentStyle={{ background: '#121826', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'white' }}
                        labelFormatter={(label) => `Question Attempt #${label}`}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="score" 
                        stroke="#6366f1" 
                        strokeWidth={3} 
                        activeDot={{ r: 6 }} 
                        dot={{ fill: '#6366f1', strokeWidth: 2, r: 4 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            {/* Bar Chart: Performance By Topic */}
            <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: '700', color: 'white' }}>Performance by Topic</h3>
              
              {metrics.topic_performance.length === 0 ? (
                <div style={{ height: '260px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px dashed var(--border-color)', borderRadius: '8px' }}>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Average scores grouped by tech stacks will display here.</p>
                </div>
              ) : (
                <div style={{ height: '260px', width: '100%' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={metrics.topic_performance} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                      <CartesianGrid stroke="rgba(255,255,255,0.02)" strokeDasharray="3 3" />
                      <XAxis dataKey="topic" stroke="var(--text-muted)" fontSize={10} tickLine={false} />
                      <YAxis domain={[0, 100]} stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                      <Tooltip 
                        contentStyle={{ background: '#121826', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'white' }}
                      />
                      <Bar dataKey="score" fill="#a855f7" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

          </div>

          {/* Weak Topics & Revision Launchpad */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
            
            {/* Left: Weak Topics & Study Recommendations */}
            <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              
              {/* Weak Topics list */}
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: '700', color: 'white', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <span>⚠️</span> Weak Areas (Scores &lt; 70)
                </h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                  Click a topic tag to jump straight to your mock preparation list.
                </p>
                
                {metrics.weak_topics.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>No weak areas detected! Excellent work.</p>
                ) : (
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {metrics.weak_topics.map((topic, idx) => (
                      <span
                        key={idx}
                        onClick={() => navigate('/interviews')}
                        style={{
                          background: 'rgba(244, 63, 94, 0.08)',
                          color: '#fda4af',
                          border: '1px solid rgba(244, 63, 94, 0.25)',
                          padding: '0.3rem 0.6rem',
                          borderRadius: '6px',
                          fontSize: '0.75rem',
                          fontWeight: '600',
                          cursor: 'pointer'
                        }}
                        title="Click to revise in Prep Portal"
                      >
                        {topic} ➔
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Revision list */}
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: '700', color: 'white', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <span>💡</span> Revision Recommendations
                </h3>
                
                {metrics.revision_topics.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Recommendations will be formulated once evaluations are computed.</p>
                ) : (
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {metrics.revision_topics.map((topic, idx) => (
                      <span
                        key={idx}
                        onClick={() => navigate('/interviews')}
                        style={{
                          background: 'rgba(245, 158, 11, 0.08)',
                          color: '#fde047',
                          border: '1px solid rgba(245, 158, 11, 0.2)',
                          padding: '0.3rem 0.6rem',
                          borderRadius: '6px',
                          fontSize: '0.75rem',
                          fontWeight: '600',
                          cursor: 'pointer'
                        }}
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Contextual Next Step Link */}
              <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.04)', display: 'flex', justifyContent: 'flex-end' }}>
                <span 
                  onClick={() => navigate('/study-plan')}
                  style={{ color: 'var(--accent-color)', fontSize: '0.85rem', fontWeight: '700', cursor: 'pointer' }}
                >
                  Go to Study Plan Roadmap ➔
                </span>
              </div>
            </div>

            {/* Right: Recent Interview Sessions Launchpad */}
            <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: '700', color: 'white' }}>Recent Interview Sessions</h3>
              
              {metrics.recent_sessions.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', border: '1px dashed var(--border-color)', borderRadius: '8px' }}>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>You haven't started any mock interview sessions yet.</p>
                  <button 
                    onClick={() => navigate('/interviews')}
                    style={{ background: 'var(--accent-color)', border: 'none', color: 'white', fontSize: '0.8rem', padding: '0.4rem 0.8rem', borderRadius: '6px', cursor: 'pointer', fontWeight: '700' }}
                  >
                    Start First Session
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {metrics.recent_sessions.map((sess) => (
                    <div 
                      key={sess.session_id} 
                      style={{
                        background: 'rgba(255,255,255,0.015)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '10px',
                        padding: '0.75rem 1rem',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <h4 style={{ fontSize: '0.85rem', fontWeight: '700', color: 'white' }}>{sess.role_title}</h4>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          {sess.started_at} • Answers: {sess.answers_count} / 9
                        </span>
                      </div>
                      
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        {sess.score !== null && (
                          <span style={{ fontSize: '0.9rem', fontWeight: '800', color: getScoreColor(sess.score) }}>
                            {sess.score}%
                          </span>
                        )}
                        
                        {sess.completed ? (
                          <span style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', border: '1px solid rgba(16, 185, 129, 0.2)', fontSize: '0.7rem', fontWeight: '700', padding: '0.2rem 0.5rem', borderRadius: '6px' }}>
                            Completed
                          </span>
                        ) : (
                          <button
                            onClick={() => navigate(`/interviews/session/${sess.session_id}`)}
                            style={{
                              background: 'rgba(245, 158, 11, 0.12)',
                              color: '#fbbf24',
                              border: '1px solid rgba(245, 158, 11, 0.25)',
                              fontSize: '0.7rem',
                              fontWeight: '700',
                              padding: '0.25rem 0.6rem',
                              borderRadius: '6px',
                              cursor: 'pointer'
                            }}
                          >
                            Resume Session ➔
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>

          {/* Module Nav Grid */}
          <div>
            <h2 className="page-title" style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>Active Modules</h2>
            <div className="grid-container">
              <div className="card" onClick={() => navigate('/resume')} style={{ cursor: 'pointer' }}>
                <div className="card-title">
                  <span style={{ fontSize: '1.5rem' }}>📄</span>
                  <span>Resume Builder</span>
                </div>
                <p className="card-desc">Optimize resume bullets and matching frequencies against target JDs.</p>
                <span style={{ display: 'inline-block', marginTop: '1rem', fontWeight: '700', fontSize: '0.85rem', color: 'var(--accent-color)' }}>Open Builder →</span>
              </div>
              <div className="card" onClick={() => navigate('/interviews')} style={{ cursor: 'pointer' }}>
                <div className="card-title">
                  <span style={{ fontSize: '1.5rem' }}>🎙️</span>
                  <span>Mock Interviews</span>
                </div>
                <p className="card-desc">Practice answering voice and text prep plan mock questions.</p>
                <span style={{ display: 'inline-block', marginTop: '1rem', fontWeight: '700', fontSize: '0.85rem', color: 'var(--accent-color)' }}>Start Interview →</span>
              </div>
              <div className="card" onClick={() => navigate('/profile')} style={{ cursor: 'pointer' }}>
                <div className="card-title">
                  <span style={{ fontSize: '1.5rem' }}>⚙️</span>
                  <span>Profile Settings</span>
                </div>
                <p className="card-desc">Configure target career pathways, job role definition, and experience levels.</p>
                <span style={{ display: 'inline-block', marginTop: '1rem', fontWeight: '700', fontSize: '0.85rem', color: 'var(--accent-color)' }}>Manage Settings →</span>
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
};

export default Dashboard;
