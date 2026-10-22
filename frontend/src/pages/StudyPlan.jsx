import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

const API_URL = 'http://127.0.0.1:8000';

const StudyPlan = () => {
  const { token } = useAuth();
  
  // State variables
  const [plan, setPlan] = useState(null);
  const [duration, setDuration] = useState(7);
  
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isUpdating, setIsUpdating] = useState({}); // tracks day id updates
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    fetchLatestPlan();
  }, []);

  const fetchLatestPlan = async () => {
    setIsLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/study-plans/latest`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        setPlan(data);
      } else {
        if (res.status !== 404) {
          setError(data.detail || 'Failed to retrieve study plan.');
        }
      }
    } catch (err) {
      console.error(err);
      setError('Connection to backend failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    setIsGenerating(true);
    setError('');
    setSuccessMsg('');
    
    try {
      const res = await fetch(`${API_URL}/study-plans`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ duration: parseInt(duration) })
      });
      
      const data = await res.json();
      if (res.ok) {
        setPlan(data);
        setSuccessMsg('Your personalized study plan has been formulated!');
      } else {
        throw new Error(data.detail || 'Failed to generate study plan.');
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'An error occurred during generation.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Toggle item in day's checklist
  const handleToggleItem = async (day, item) => {
    const dayId = day.id;
    const isCompleted = day.completed_items.includes(item);
    
    // Compute new completed items list
    const newCompleted = isCompleted
      ? day.completed_items.filter(i => i !== item)
      : [...day.completed_items, item];

    // Optimistic UI state update
    const updatedDays = plan.days.map(d => {
      if (d.id === dayId) {
        return { ...d, completed_items: newCompleted };
      }
      return d;
    });
    setPlan(prev => ({ ...prev, days: updatedDays }));

    setIsUpdating(prev => ({ ...prev, [dayId]: true }));
    try {
      const res = await fetch(`${API_URL}/study-plan-days/${dayId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ completed_items: newCompleted })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to save checkbox update.');
      }
    } catch (err) {
      console.error(err);
      setError('Failed to persist progress changes. Please refresh.');
      // Revert optimistic update
      fetchLatestPlan();
    } finally {
      setIsUpdating(prev => ({ ...prev, [dayId]: false }));
    }
  };

  // Calculate total progress
  const getProgressStats = () => {
    if (!plan || !plan.days) return { total: 0, completed: 0, pct: 0 };
    let total = 0;
    let completed = 0;
    
    plan.days.forEach(d => {
      total += d.action_items.length;
      completed += d.completed_items.length;
    });

    const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
    return { total, completed, pct };
  };

  const { total, completed, pct } = getProgressStats();

  return (
    <div className="dashboard-container" style={{ alignSelf: 'flex-start', margin: '2rem auto', maxWidth: '1000px', width: '95%' }}>
      
      {/* Header */}
      <div className="page-header" style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">Personal Study Plan</h1>
          <p className="page-subtitle">Custom daily tasks targeting matching gaps and weak areas</p>
        </div>
        
        {plan && (
          <button
            onClick={() => {
              if (window.confirm("Regenerate study plan? This will wipe your checked tasks and build a new timeline using latest evaluations.")) {
                setPlan(null);
                setSuccessMsg('');
              }
            }}
            className="submit-btn"
            style={{
              width: 'auto',
              padding: '0 1rem',
              height: '38px',
              fontSize: '0.85rem',
              background: 'none',
              border: '1px solid var(--border-color)',
              color: 'var(--text-secondary)'
            }}
          >
            🔄 Refresh Plan
          </button>
        )}
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
          <p style={{ color: 'var(--text-secondary)' }}>Loading study plan...</p>
        </div>
      ) : !plan ? (
        /* Empty State: Create Study Plan Form */
        <div style={{ maxWidth: '600px', margin: '0 auto' }}>
          <div className="card" style={{ padding: '2.5rem 2rem', textAlign: 'center', background: 'rgba(18, 24, 38, 0.5)' }}>
            <span style={{ fontSize: '3.5rem', display: 'block', marginBottom: '1rem' }}>📅</span>
            <h2 className="card-title" style={{ fontSize: '1.5rem', marginBottom: '0.75rem' }}>Build Your Study Roadmap</h2>
            <p className="card-desc" style={{ marginBottom: '2rem', fontSize: '0.95rem' }}>
              We will scan your matching gaps and weak areas to generate a balanced study schedule populated with short, realistically achievable daily tasks.
            </p>

            <form onSubmit={handleGenerate} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', textAlign: 'left' }}>
              <div className="form-group">
                <label className="form-label" style={{ fontWeight: '600' }}>Select Schedule Duration</label>
                <select 
                  className="form-input" 
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                  style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)', color: 'white' }}
                >
                  <option value={7}>7 Days (Short sprint)</option>
                  <option value={14}>14 Days (Balanced path)</option>
                  <option value={30}>30 Days (Comprehensive prep)</option>
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
                    <span>Composing study days...</span>
                  </>
                ) : (
                  <span>Build Study Plan</span>
                )}
              </button>
            </form>
          </div>
        </div>
      ) : (
        /* Plan checklist grid display */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Progress Tracker Card */}
          <div className="card" style={{ background: 'rgba(99, 102, 241, 0.05)', border: '1px solid rgba(99, 102, 241, 0.15)', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'white' }}>
                  📈 Prep Progress: {plan.duration} Days Timeline
                </h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  Completed {completed} of {total} total roadmap tasks
                </span>
              </div>
              <span style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--accent-color)' }}>
                {pct}%
              </span>
            </div>

            {/* Progress Bar */}
            <div style={{ height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
              <div 
                style={{ 
                  height: '100%', 
                  width: `${pct}%`, 
                  background: 'var(--accent-gradient)',
                  borderRadius: '4px',
                  transition: 'width 0.4s ease-out'
                }} 
              />
            </div>
          </div>

          {/* Daily Calendar Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.25rem' }}>
            {plan.days.map((day) => {
              const dayCompleted = day.completed_items.length === day.action_items.length;
              return (
                <div 
                  key={day.id} 
                  className="card"
                  style={{
                    padding: '1.25rem',
                    background: dayCompleted ? 'rgba(16, 185, 129, 0.02)' : 'rgba(255,255,255,0.012)',
                    borderColor: dayCompleted ? 'rgba(16, 185, 129, 0.25)' : 'var(--border-color)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                    transition: 'border-color 0.3s'
                  }}
                >
                  {/* Day Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: '800', color: 'var(--text-secondary)' }}>
                      Day {day.day_number}
                    </span>
                    {dayCompleted && (
                      <span style={{ background: 'rgba(16, 185, 129, 0.12)', color: 'var(--success)', border: '1px solid rgba(16, 185, 129, 0.25)', fontSize: '0.65rem', fontWeight: '700', padding: '0.15rem 0.4rem', borderRadius: '4px', textTransform: 'uppercase' }}>
                        ✓ Done
                      </span>
                    )}
                  </div>

                  {/* Day Theme */}
                  <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'white', lineHeight: '1.4' }}>
                    {day.theme}
                  </h3>

                  {/* Checklist items */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
                    {day.action_items.map((item, idx) => {
                      const itemChecked = day.completed_items.includes(item);
                      return (
                        <div 
                          key={idx}
                          onClick={() => handleToggleItem(day, item)}
                          style={{
                            display: 'flex',
                            gap: '0.5rem',
                            alignItems: 'flex-start',
                            cursor: 'pointer',
                            padding: '0.4rem',
                            borderRadius: '6px',
                            background: itemChecked ? 'rgba(255,255,255,0.01)' : 'none',
                            transition: 'background 0.2s'
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={itemChecked}
                            readOnly
                            style={{ 
                              cursor: 'pointer', 
                              marginTop: '0.15rem',
                              accentColor: 'var(--accent-color)'
                            }}
                          />
                          <span 
                            style={{ 
                              fontSize: '0.8rem', 
                              lineHeight: '1.4',
                              color: itemChecked ? 'var(--text-muted)' : 'var(--text-primary)',
                              textDecoration: itemChecked ? 'line-through' : 'none',
                              transition: 'color 0.2s'
                            }}
                          >
                            {item}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>

        </div>
      )}
    </div>
  );
};

export default StudyPlan;
