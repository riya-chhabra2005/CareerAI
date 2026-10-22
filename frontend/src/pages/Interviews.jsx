import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

import { API_URL } from '../config';

const Interviews = () => {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  
  // State variables
  const [plan, setPlan] = useState(null);
  const [isStartingSession, setIsStartingSession] = useState(false);
  const [resumes, setResumes] = useState([]);
  const [jds, setJds] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [selectedJdId, setSelectedJdId] = useState('');
  
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleStartMockInterview = async () => {
    if (!plan) return;
    setIsStartingSession(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/interviews/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ plan_id: plan.id })
      });
      const data = await res.json();
      if (res.ok) {
        navigate(`/interviews/session/${data.id}`);
      } else {
        setError(data.detail || 'Failed to start interview session.');
      }
    } catch (err) {
      console.error(err);
      setError('Connection to backend failed.');
    } finally {
      setIsStartingSession(false);
    }
  };

  // Fetch plan and documents on mount
  useEffect(() => {
    fetchLatestPlan();
  }, []);

  const fetchLatestPlan = async () => {
    setIsLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/interview-plans/latest`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await res.json();
      if (res.ok) {
        setPlan(data);
      } else {
        // Plan not found or other errors
        if (res.status === 404) {
          // If no plan, fetch user's resumes and JDs for selection
          await fetchDocuments();
        } else {
          setError(data.detail || 'Failed to fetch interview plan.');
        }
      }
    } catch (err) {
      console.error(err);
      setError('Connection to backend failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDocuments = async () => {
    try {
      const [resumesRes, jdsRes] = await Promise.all([
        fetch(`${API_URL}/resumes`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/jd`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (resumesRes.ok && jdsRes.ok) {
        const resumesData = await resumesRes.json();
        const jdsData = await jdsRes.json();
        setResumes(resumesData);
        setJds(jdsData);
        
        // Auto-select latest if available
        if (resumesData.length > 0) setSelectedResumeId(resumesData[0].id);
        if (jdsData.length > 0) setSelectedJdId(jdsData[0].id);
      }
    } catch (err) {
      console.error('Error fetching documents:', err);
    }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!selectedResumeId || !selectedJdId) {
      setError('Please select both a resume and a job description to prepare.');
      return;
    }

    setIsGenerating(true);
    setError('');
    setSuccessMsg('');

    try {
      const res = await fetch(`${API_URL}/interview-plans`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          resume_id: parseInt(selectedResumeId),
          jd_id: parseInt(selectedJdId)
        })
      });

      const data = await res.json();
      if (res.ok) {
        setPlan(data);
        setSuccessMsg('Personalized prep plan generated successfully!');
      } else {
        throw new Error(data.detail || 'Failed to generate plan.');
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'An error occurred during generation.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Group questions by type
  const getQuestionsByType = (type) => {
    if (!plan || !plan.questions) return [];
    return plan.questions.filter(q => q.type === type);
  };

  const getDifficultyColor = (diff) => {
    const d = diff.toLowerCase();
    if (d === 'easy') return '#10b981'; // success green
    if (d === 'medium') return '#fb541b'; // warning orange
    return '#f43f5e'; // error red
  };

  return (
    <div className="dashboard-container" style={{ alignSelf: 'flex-start', margin: '2rem auto', maxWidth: '1200px', width: '95%' }}>
      <div className="page-header">
        <h1 className="page-title">Personalized Prep Portal</h1>
        <p className="page-subtitle">Custom-tailored questions focusing on your strengths and skill gaps</p>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="alert alert-success" style={{ marginBottom: '1.5rem', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
          <span>✅</span>
          <span>{successMsg}</span>
        </div>
      )}

      {isLoading ? (
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
          <div className="spinner" style={{ width: '40px', height: '40px', borderThickness: '4px', marginBottom: '1.25rem' }}></div>
          <p style={{ color: 'var(--text-secondary)' }}>Loading prep dashboard...</p>
        </div>
      ) : !plan ? (
        /* Empty State: Prompt to generate plan */
        <div style={{ maxWidth: '650px', margin: '0 auto' }}>
          <div className="card" style={{ padding: '2.5rem 2rem', textAlign: 'center', background: 'rgba(18, 24, 38, 0.5)' }}>
            <span style={{ fontSize: '3.5rem', display: 'block', marginBottom: '1rem' }}>🎙️</span>
            <h2 className="card-title" style={{ fontSize: '1.5rem', marginBottom: '0.75rem' }}>Create Your Interview Preparation Plan</h2>
            <p className="card-desc" style={{ marginBottom: '2rem', fontSize: '0.95rem' }}>
              We will scan your resume against the target job requirements and compose 9 targeted conceptual, coding, and behavioral questions weighted towards your skill gaps.
            </p>

            {resumes.length === 0 || jds.length === 0 ? (
              <div style={{ background: 'rgba(244, 63, 94, 0.05)', border: '1px solid rgba(244, 63, 94, 0.15)', borderRadius: '12px', padding: '1.5rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
                <div>
                  <p style={{ color: '#fda4af', fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.5rem' }}>⚠️ Missing Setup Documents</p>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    You must upload at least one Resume and one target Job Description in the **Resume Optimizer** module before generating a prep plan.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => navigate('/resume')}
                  className="submit-btn"
                  style={{ width: 'auto', padding: '0 1.25rem', height: '40px', fontSize: '0.85rem' }}
                >
                  Go to Resume Optimizer ➔
                </button>
              </div>
            ) : (
              <form onSubmit={handleGenerate} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', textAlign: 'left' }}>
                <div className="form-group">
                  <label className="form-label" style={{ fontWeight: '600' }}>Select Resume Profile</label>
                  <select 
                    className="form-input" 
                    value={selectedResumeId}
                    onChange={(e) => setSelectedResumeId(e.target.value)}
                    style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)', color: 'white' }}
                  >
                    {resumes.map(r => (
                      <option key={r.id} value={r.id}>
                        {r.filename} ({new Date(r.created_at).toLocaleDateString()})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label" style={{ fontWeight: '600' }}>Select Target Job Description</label>
                  <select 
                    className="form-input"
                    value={selectedJdId}
                    onChange={(e) => setSelectedJdId(e.target.value)}
                    style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)', color: 'white' }}
                  >
                    {jds.map(j => (
                      <option key={j.id} value={j.id}>
                        {j.role_title} ({new Date(j.created_at).toLocaleDateString()})
                      </option>
                    ))}
                  </select>
                </div>

                <button 
                  type="submit" 
                  className="submit-btn" 
                  disabled={isGenerating}
                  style={{ marginTop: '1rem', width: '100%', height: '48px', fontSize: '1rem' }}
                >
                  {isGenerating ? (
                    <>
                      <div className="spinner" style={{ marginRight: '0.5rem' }}></div>
                      <span>Analyzing gaps and formulating questions...</span>
                    </>
                  ) : (
                    <span>Generate Prep Plan</span>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>
      ) : (
        /* Plan display state */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Header Panel */}
          <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(168, 85, 247, 0.08) 100%)' }}>
            <div>
              <h2 className="card-title" style={{ fontSize: '1.4rem', marginBottom: '0.25rem' }}>
                🎯 Target Prep: {plan.role_title}
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Generated on {new Date(plan.created_at).toLocaleDateString()} at {new Date(plan.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
              </p>
            </div>
            
            <button
              onClick={handleStartMockInterview}
              disabled={isStartingSession}
              className="submit-btn"
              style={{
                width: 'auto',
                padding: '0 1.5rem',
                height: '42px',
                fontSize: '0.9rem',
                fontWeight: '700',
                background: 'var(--accent-gradient)'
              }}
            >
              {isStartingSession ? 'Starting...' : '🎙️ Start Mock Interview'}
            </button>
          </div>

          {/* Three Column Grid layout */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
            
            {/* Column 1: Technical Questions */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '2px solid rgba(99, 102, 241, 0.3)', paddingBottom: '0.5rem' }}>
                <span style={{ fontSize: '1.25rem' }}>⚙️</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: '700' }}>Technical Concepts</h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {getQuestionsByType('technical').map((q, idx) => (
                  <div key={q.id} className="card" style={{ padding: '1.25rem', background: 'rgba(255,255,255,0.015)' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', padding: '0.15rem 0.5rem', borderRadius: '4px', background: 'rgba(99, 102, 241, 0.15)', color: '#a5b4fc' }}>
                        {q.topic_tag}
                      </span>
                      <span style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', padding: '0.15rem 0.5rem', borderRadius: '4px', background: `${getDifficultyColor(q.difficulty)}20`, color: getDifficultyColor(q.difficulty) }}>
                        {q.difficulty}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.9rem', lineHeight: '1.5', color: 'var(--text-primary)' }}>
                      {q.question_text}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Column 2: Coding Questions */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '2px solid rgba(168, 85, 247, 0.3)', paddingBottom: '0.5rem' }}>
                <span style={{ fontSize: '1.25rem' }}>💻</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: '700' }}>Coding & Algorithms</h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {getQuestionsByType('coding').map((q, idx) => (
                  <div key={q.id} className="card" style={{ padding: '1.25rem', background: 'rgba(255,255,255,0.015)' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', padding: '0.15rem 0.5rem', borderRadius: '4px', background: 'rgba(168, 85, 247, 0.15)', color: '#e9d5ff' }}>
                        {q.topic_tag}
                      </span>
                      <span style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', padding: '0.15rem 0.5rem', borderRadius: '4px', background: `${getDifficultyColor(q.difficulty)}20`, color: getDifficultyColor(q.difficulty) }}>
                        {q.difficulty}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.9rem', lineHeight: '1.5', color: 'var(--text-primary)' }}>
                      {q.question_text}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Column 3: HR / Behavioral Questions */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '2px solid rgba(16, 185, 129, 0.3)', paddingBottom: '0.5rem' }}>
                <span style={{ fontSize: '1.25rem' }}>🗣️</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: '700' }}>HR & Behavioral</h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {getQuestionsByType('hr').map((q, idx) => (
                  <div key={q.id} className="card" style={{ padding: '1.25rem', background: 'rgba(255,255,255,0.015)' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', padding: '0.15rem 0.5rem', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.15)', color: '#a7f3d0' }}>
                        {q.topic_tag}
                      </span>
                      <span style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', padding: '0.15rem 0.5rem', borderRadius: '4px', background: `${getDifficultyColor(q.difficulty)}20`, color: getDifficultyColor(q.difficulty) }}>
                        {q.difficulty}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.9rem', lineHeight: '1.5', color: 'var(--text-primary)' }}>
                      {q.question_text}
                    </p>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* Regeneration option */}
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1.5rem' }}>
            <button
              onClick={async () => {
                if (window.confirm("Are you sure you want to regenerate your prep plan? This will create a fresh set of questions based on your latest files.")) {
                  setPlan(null);
                  await fetchDocuments();
                }
              }}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                fontSize: '0.85rem',
                cursor: 'pointer',
                textDecoration: 'underline'
              }}
            >
              🔄 Generate a different prep plan
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Interviews;
