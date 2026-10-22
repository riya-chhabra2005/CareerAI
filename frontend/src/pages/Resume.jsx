import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const API_URL = 'http://127.0.0.1:8000';

const Resume = () => {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  
  // Input states
  const [resumeMode, setResumeMode] = useState('upload'); // 'upload' or 'paste'
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeText, setResumeText] = useState('');
  
  const [jdMode, setJdMode] = useState('paste'); // 'paste' or 'upload'
  const [jdFile, setJdFile] = useState(null);
  const [jdText, setJdText] = useState('');
  const [roleTitle, setRoleTitle] = useState(user?.target_job_role || 'Software Engineer');
  
  // Loading & error states
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isParsingJd, setIsParsingJd] = useState(false);
  const [error, setError] = useState('');
  
  // Analysis result state
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState('match'); // 'match' or 'ats'

  // Saved states from DB
  const [savedResume, setSavedResume] = useState(null);
  const [savedJd, setSavedJd] = useState(null);
  const [isLoadingSaved, setIsLoadingSaved] = useState(false);

  // Fetch saved resume & JD on mount
  useEffect(() => {
    const fetchSavedData = async () => {
      if (!token) return;
      setIsLoadingSaved(true);
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

          if (resumesData.length > 0) {
            const latestResume = resumesData[0];
            setSavedResume(latestResume);
            if (latestResume.filename === 'pasted_resume.txt') {
              setResumeMode('paste');
              setResumeText(latestResume.raw_text);
            } else {
              setResumeMode('upload');
            }
          }

          if (jdsData.length > 0) {
            const latestJd = jdsData[0];
            setSavedJd(latestJd);
            setRoleTitle(latestJd.role_title);
            setJdText(latestJd.raw_jd_text);
            setJdMode('paste');
          }
        }
      } catch (err) {
        console.error("Error fetching saved resume/JD:", err);
      } finally {
        setIsLoadingSaved(false);
      }
    };

    fetchSavedData();
  }, [token]);

  const handleFileChange = (e, setFile, setText) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setFile(file);
  };

  const handleJdFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setJdFile(file);
    setIsParsingJd(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_URL}/jd/parse`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to parse Job Description file');
      }

      if (data.role_title) {
        setRoleTitle(data.role_title);
      }
      if (data.raw_jd_text) {
        setJdText(data.raw_jd_text);
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'Error parsing Job Description file.');
    } finally {
      setIsParsingJd(false);
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);

    // Validations
    if (resumeMode === 'upload' && !resumeFile && !savedResume) {
      setError('Please select a resume file to upload.');
      return;
    }
    if (resumeMode === 'paste' && !resumeText.trim()) {
      setError('Please paste your resume text.');
      return;
    }
    if (jdMode === 'upload' && !jdFile && !savedJd) {
      setError('Please select a job description file.');
      return;
    }
    if (jdMode === 'paste' && !jdText.trim()) {
      setError('Please paste the job description text.');
      return;
    }
    if (!roleTitle.trim()) {
      setError('Please specify the role title.');
      return;
    }

    setIsAnalyzing(true);

    try {
      // 1. Upload/save resume (or reuse saved)
      let resumeId = null;
      
      const isResumeUnchanged = 
        (resumeMode === 'upload' && !resumeFile && savedResume && savedResume.filename !== 'pasted_resume.txt') ||
        (resumeMode === 'paste' && savedResume && resumeText === savedResume.raw_text);

      if (isResumeUnchanged) {
        resumeId = savedResume.id;
      } else {
        const resumeFormData = new FormData();
        if (resumeMode === 'upload') {
          resumeFormData.append('file', resumeFile);
        } else {
          resumeFormData.append('pasted_text', resumeText);
        }

        const resumeRes = await fetch(`${API_URL}/resumes`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: resumeFormData
        });

        const resumeData = await resumeRes.json();
        if (!resumeRes.ok) {
          throw new Error(resumeData.detail || 'Failed to upload resume');
        }
        resumeId = resumeData.id;
        setSavedResume(resumeData);
        setResumeFile(null); // Reset file selection to show "Saved" state
      }

      // 2. Upload job description (or reuse saved)
      let jdId = null;
      let finalJdText = jdText;

      const isJdUnchanged = 
        savedJd && 
        roleTitle === savedJd.role_title && 
        finalJdText === savedJd.raw_jd_text;

      if (isJdUnchanged) {
        jdId = savedJd.id;
      } else {
        const jdRes = await fetch(`${API_URL}/jd`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            role_title: roleTitle,
            raw_jd_text: finalJdText
          })
        });

        const jdData = await jdRes.json();
        if (!jdRes.ok) {
          throw new Error(jdData.detail || 'Failed to save job description');
        }
        jdId = jdData.id;
        setSavedJd(jdData);
        setJdFile(null);
      }

      // 3. Compute ATS score
      const scoreRes = await fetch(`${API_URL}/resumes/${resumeId}/ats-score?jd_id=${jdId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const scoreData = await scoreRes.json();
      if (!scoreRes.ok) {
        throw new Error(scoreData.detail || 'Failed to calculate ATS score');
      }

      // 4. Fetch Match & Suggestions in parallel
      const [matchRes, suggestionsRes] = await Promise.all([
        fetch(`${API_URL}/resumes/${resumeId}/match`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ jd_id: jdId })
        }),
        fetch(`${API_URL}/resumes/${resumeId}/suggestions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ jd_id: jdId })
        })
      ]);

      const matchData = await matchRes.json();
      if (!matchRes.ok) {
        throw new Error(matchData.detail || 'Failed to calculate Resume-JD match score');
      }

      const suggestionsData = await suggestionsRes.json();
      if (!suggestionsRes.ok) {
        throw new Error(suggestionsData.detail || 'Failed to generate suggestions');
      }

      setResult({
        ats: scoreData,
        match: matchData,
        suggestions: suggestionsData.suggestions
      });
      setActiveTab('match');
    } catch (err) {
      console.error(err);
      setError(err.message || 'An error occurred during analysis.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getScoreColorClass = (score) => {
    if (score >= 75) return 'score-green';
    if (score >= 50) return 'score-yellow';
    return 'score-red';
  };

  return (
    <div className="dashboard-container" style={{ alignSelf: 'flex-start', margin: '2rem auto', maxWidth: '1100px' }}>
      <div className="page-header">
        <h1 className="page-title">ATS Optimizer</h1>
        <p className="page-subtitle">Match your resume against job descriptions to increase your interview rates</p>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
          <span style={{ fontSize: '1.15rem' }}>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {isLoadingSaved && (
        <div className="alert alert-info" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div className="spinner" style={{ width: '16px', height: '16px', borderThickness: '2px', margin: 0 }}></div>
          <span>Loading saved resume and job description...</span>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '2rem' }}>
        {/* Left Side inputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h2 className="card-title" style={{ margin: 0 }}>1. Upload Resume</h2>
              {savedResume && (
                <span style={{
                  fontSize: '0.75rem',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '12px',
                  background: 'rgba(74, 222, 128, 0.1)',
                  color: 'rgb(74, 222, 128)',
                  border: '1px solid rgba(74, 222, 128, 0.2)',
                  fontWeight: '600'
                }}>
                  ✓ Saved Resume Loaded
                </span>
              )}
            </div>
            
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.25rem' }}>
              <button 
                type="button"
                className="nav-auth-btn"
                style={{ 
                  background: resumeMode === 'upload' ? 'var(--accent-gradient)' : 'rgba(255,255,255,0.03)',
                  border: '1px solid var(--border-color)',
                  color: 'white',
                  flex: 1
                }}
                onClick={() => setResumeMode('upload')}
              >
                Upload File (.pdf, .txt)
              </button>
              <button 
                type="button"
                className="nav-auth-btn"
                style={{ 
                  background: resumeMode === 'paste' ? 'var(--accent-gradient)' : 'rgba(255,255,255,0.03)',
                  border: '1px solid var(--border-color)',
                  color: 'white',
                  flex: 1
                }}
                onClick={() => setResumeMode('paste')}
              >
                Paste Plain Text
              </button>
            </div>

            {resumeMode === 'upload' ? (
              <div style={{
                border: '2px dashed var(--border-color)',
                borderRadius: '12px',
                padding: '2rem 1rem',
                textAlign: 'center',
                cursor: 'pointer',
                background: 'rgba(9, 13, 22, 0.2)',
                position: 'relative'
              }}>
                <input 
                  type="file" 
                  accept=".pdf,.txt"
                  style={{
                    position: 'absolute',
                    top: 0, left: 0, width: '100%', height: '100%',
                    opacity: 0, cursor: 'pointer'
                  }}
                  onChange={(e) => handleFileChange(e, setResumeFile, setResumeText)}
                />
                <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: '0.5rem' }}>📤</span>
                <span style={{ fontWeight: '600', color: 'var(--text-primary)', display: 'block' }}>
                  {resumeFile ? resumeFile.name : (savedResume && savedResume.filename !== 'pasted_resume.txt' ? `📄 ${savedResume.filename} (Saved)` : 'Select PDF or TXT file')}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {savedResume && savedResume.filename !== 'pasted_resume.txt' && !resumeFile 
                    ? `Saved on ${new Date(savedResume.created_at).toLocaleDateString()}` 
                    : 'Max file size 5MB'}
                </span>
              </div>
            ) : (
              <textarea
                className="form-input"
                style={{ minHeight: '160px', fontFamily: 'monospace', fontSize: '0.85rem' }}
                placeholder="Paste the full text of your resume here..."
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
              />
            )}
          </div>

          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h2 className="card-title" style={{ margin: 0 }}>2. Target Job Description</h2>
              {savedJd && (
                <span style={{
                  fontSize: '0.75rem',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '12px',
                  background: 'rgba(74, 222, 128, 0.1)',
                  color: 'rgb(74, 222, 128)',
                  border: '1px solid rgba(74, 222, 128, 0.2)',
                  fontWeight: '600'
                }}>
                  ✓ Saved JD Loaded
                </span>
              )}
            </div>
            
            <div className="form-group">
              <label className="form-label">Role Title</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Backend Developer"
                value={roleTitle}
                onChange={(e) => setRoleTitle(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.25rem' }}>
              <button 
                type="button"
                className="nav-auth-btn"
                style={{ 
                  background: jdMode === 'paste' ? 'var(--accent-gradient)' : 'rgba(255,255,255,0.03)',
                  border: '1px solid var(--border-color)',
                  color: 'white',
                  flex: 1
                }}
                onClick={() => setJdMode('paste')}
              >
                Paste JD Text
              </button>
              <button 
                type="button"
                className="nav-auth-btn"
                style={{ 
                  background: jdMode === 'upload' ? 'var(--accent-gradient)' : 'rgba(255,255,255,0.03)',
                  border: '1px solid var(--border-color)',
                  color: 'white',
                  flex: 1
                }}
                onClick={() => setJdMode('upload')}
              >
                Upload File (.pdf, .txt)
              </button>
            </div>

            {jdMode === 'paste' ? (
              <textarea
                className="form-input"
                style={{ minHeight: '140px', fontSize: '0.9rem' }}
                placeholder="Paste the target job description requirements here..."
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
              />
            ) : (
              <div style={{
                border: '2px dashed var(--border-color)',
                borderRadius: '12px',
                padding: '1.5rem 1rem',
                textAlign: 'center',
                cursor: 'pointer',
                background: 'rgba(9, 13, 22, 0.2)',
                position: 'relative'
              }}>
                {isParsingJd ? (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0' }}>
                    <div className="spinner" style={{ width: '24px', height: '24px', borderWidth: '2px', borderStyle: 'solid', borderColor: 'var(--accent-color) transparent transparent transparent', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: 0 }}></div>
                    <span style={{ color: 'var(--text-primary)', fontSize: '0.9rem', fontWeight: '500' }}>Parsing JD and extracting Role Title...</span>
                  </div>
                ) : (
                  <>
                    <input 
                      type="file" 
                      accept=".pdf,.txt"
                      style={{
                        position: 'absolute',
                        top: 0, left: 0, width: '100%', height: '100%',
                        opacity: 0, cursor: 'pointer'
                      }}
                      onChange={handleJdFileChange}
                    />
                    <span style={{ fontSize: '2rem', display: 'block', marginBottom: '0.5rem' }}>📝</span>
                    <span style={{ fontWeight: '600', color: 'var(--text-primary)', display: 'block' }}>
                      {jdFile ? jdFile.name : (savedJd ? `📄 Saved JD File` : 'Select target JD file (.pdf, .txt)')}
                    </span>
                  </>
                )}
              </div>
            )}

            <button 
              type="button" 
              className="submit-btn" 
              onClick={handleAnalyze} 
              disabled={isAnalyzing || isParsingJd}
              style={{ marginTop: '1.5rem' }}
            >
              {isAnalyzing ? (
                <>
                  <div className="spinner"></div>
                  <span>Analyzing Compatibility...</span>
                </>
              ) : (
                <span>Analyze Resume Match</span>
              )}
            </button>
          </div>
        </div>

        {/* Right Side results */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {!result && !isAnalyzing && (
            <div className="card" style={{ 
              display: 'flex', 
              flexDirection: 'column', 
              justifyContent: 'center', 
              alignItems: 'center', 
              textAlign: 'center',
              minHeight: '400px',
              borderStyle: 'dashed'
            }}>
              <span style={{ fontSize: '4rem', marginBottom: '1.5rem', opacity: 0.7 }}>📊</span>
              <h3 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '0.5rem' }}>Awaiting Analysis</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', maxWidth: '300px' }}>
                Upload your resume and the target job description to compute your real-time compatibility score.
              </p>
            </div>
          )}

          {isAnalyzing && (
            <div className="card" style={{ 
              display: 'flex', 
              flexDirection: 'column', 
              justifyContent: 'center', 
              alignItems: 'center', 
              textAlign: 'center',
              minHeight: '400px'
            }}>
              <div className="spinner" style={{ width: '45px', height: '45px', borderThickness: '4px', marginBottom: '1.5rem' }}></div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '0.5rem' }}>Parsing Documents...</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', maxWidth: '300px' }}>
                Analyzing formatting rules, section headings, machine-readability, dates, and keyword density.
              </p>
            </div>
          )}

          {result && !isAnalyzing && (
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {/* Tab Selector */}
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
                <button
                  type="button"
                  className="nav-auth-btn"
                  style={{
                    background: activeTab === 'match' ? 'var(--accent-gradient)' : 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-color)',
                    color: 'white',
                    flex: 1,
                    fontSize: '0.85rem',
                    padding: '0.5rem 0.75rem',
                    cursor: 'pointer'
                  }}
                  onClick={() => setActiveTab('match')}
                >
                  🎯 Job Fit & Skill Gaps
                </button>
                <button
                  type="button"
                  className="nav-auth-btn"
                  style={{
                    background: activeTab === 'suggestions' ? 'var(--accent-gradient)' : 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-color)',
                    color: 'white',
                    flex: 1,
                    fontSize: '0.85rem',
                    padding: '0.5rem 0.75rem',
                    cursor: 'pointer'
                  }}
                  onClick={() => setActiveTab('suggestions')}
                >
                  💡 Mentor Suggestions
                </button>
                <button
                  type="button"
                  className="nav-auth-btn"
                  style={{
                    background: activeTab === 'ats' ? 'var(--accent-gradient)' : 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-color)',
                    color: 'white',
                    flex: 1,
                    fontSize: '0.85rem',
                    padding: '0.5rem 0.75rem',
                    cursor: 'pointer'
                  }}
                  onClick={() => setActiveTab('ats')}
                >
                  📋 ATS Formatting Check
                </button>
              </div>

              {activeTab === 'match' ? (
                /* Tab 1: Resume-JD Match Score & Skills Gap Analysis */
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem', paddingBottom: '1.25rem', borderBottom: '1px solid var(--border-color)' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-secondary)' }}>Overall Compatibility</h3>
                    
                    {/* Score circle */}
                    <div 
                      className={`score-radial-wrapper ${getScoreColorClass(result.match.match_score)}`}
                      style={{
                        width: '130px',
                        height: '130px',
                        borderRadius: '50%',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center',
                        position: 'relative',
                        boxShadow: '0 10px 25px rgba(0,0,0,0.4)'
                      }}
                    >
                      <span style={{ fontSize: '2.5rem', fontWeight: '800', fontFamily: 'var(--font-heading)' }}>
                        {result.match.match_score}%
                      </span>
                      <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1px', opacity: 0.8 }}>
                        Match
                      </span>
                    </div>

                    <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      <span>TF-IDF: <strong>{result.match.tfidf_score}%</strong></span>
                      <span>Semantic: <strong>{result.match.semantic_score}%</strong></span>
                    </div>
                    
                    <p style={{ 
                      fontSize: '0.9rem', 
                      textAlign: 'center', 
                      fontWeight: '600',
                      color: result.match.match_score >= 75 ? 'var(--success)' : result.match.match_score >= 50 ? 'var(--warning)' : 'var(--error)'
                    }}>
                      {result.match.match_score >= 75 ? 'Excellent Job Match!' : result.match.match_score >= 50 ? 'Good Match with Gaps' : 'Significant Skill Gap'}
                    </p>
                  </div>

                  {/* Skills Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    {/* Matched Skills Column */}
                    <div>
                      <h4 className="form-label" style={{ marginBottom: '0.5rem', color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.85rem' }}>
                        <span>✅</span> Matched ({result.match.matched_skills.length})
                      </h4>
                      {result.match.matched_skills.length === 0 ? (
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No matching skills found.</p>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                          {result.match.matched_skills.map((skill, idx) => (
                            <div 
                              key={idx} 
                              style={{
                                background: 'rgba(16, 185, 129, 0.05)',
                                border: '1px solid rgba(16, 185, 129, 0.15)',
                                borderRadius: '6px',
                                padding: '0.4rem 0.6rem',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                fontSize: '0.8rem'
                              }}
                            >
                              <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{skill.name}</span>
                              <span style={{ color: 'var(--success)', fontSize: '0.7rem', opacity: 0.9 }}>
                                {skill.frequency}x
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Missing Skills Column */}
                    <div>
                      <h4 className="form-label" style={{ marginBottom: '0.5rem', color: 'var(--error)', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.85rem' }}>
                        <span>⚠️</span> Missing ({result.match.missing_skills.length})
                      </h4>
                      {result.match.missing_skills.length === 0 ? (
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No missing skills detected!</p>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                          {result.match.missing_skills.map((skill, idx) => {
                            const isImportant = skill.frequency >= 2;
                            return (
                              <div 
                                key={idx} 
                                style={{
                                  background: isImportant ? 'rgba(244, 63, 94, 0.08)' : 'rgba(255, 255, 255, 0.01)',
                                  border: isImportant ? '1px solid rgba(244, 63, 94, 0.35)' : '1px solid var(--border-color)',
                                  borderRadius: '6px',
                                  padding: '0.4rem 0.6rem',
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center',
                                  fontSize: '0.8rem',
                                  boxShadow: isImportant ? '0 0 6px rgba(244, 63, 94, 0.08)' : 'none'
                                }}
                              >
                                <span style={{ fontWeight: '600', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                                  {isImportant && <span style={{ color: 'var(--error)', fontWeight: 'bold' }}>•</span>}
                                  {skill.name}
                                </span>
                                <span 
                                  style={{ 
                                    color: isImportant ? 'var(--error)' : 'var(--text-muted)', 
                                    fontSize: '0.7rem', 
                                    fontWeight: isImportant ? '700' : 'normal' 
                                  }}
                                >
                                  {isImportant ? 'Critical' : `Count: ${skill.frequency}`}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : activeTab === 'suggestions' ? (
                /* Tab 2: Mentor Suggestions Panel */
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  <div style={{ paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-secondary)' }}>Mentor Improvement Advice</h3>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                      Actionable feedback tailored to ground your resume experience in the JD requirements.
                    </p>
                  </div>
                  
                  {result.suggestions.length === 0 ? (
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>
                      No improvement suggestions needed — your resume is highly optimized!
                    </p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      {result.suggestions.map((sug, idx) => {
                        const isWording = sug.category === 'Wording';
                        const isQuantify = sug.category === 'Quantify Your Impact';
                        
                        return (
                          <div 
                            key={idx}
                            style={{
                              background: 'rgba(255, 255, 255, 0.02)',
                              border: '1px solid var(--border-color)',
                              borderRadius: '12px',
                              padding: '1rem',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '0.75rem'
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span 
                                style={{
                                  background: isWording ? 'rgba(99, 102, 241, 0.15)' : isQuantify ? 'rgba(245, 158, 11, 0.15)' : 'rgba(168, 85, 247, 0.15)',
                                  color: isWording ? '#818cf8' : isQuantify ? '#fbbf24' : '#c084fc',
                                  fontSize: '0.75rem',
                                  fontWeight: '700',
                                  padding: '0.2rem 0.6rem',
                                  borderRadius: '6px',
                                  textTransform: 'uppercase',
                                  letterSpacing: '0.5px'
                                }}
                              >
                                {sug.category}
                              </span>
                              
                              {sug.requires_verification && (
                                <span 
                                  style={{
                                    background: 'rgba(244, 63, 94, 0.15)',
                                    color: '#fb7185',
                                    fontSize: '0.7rem',
                                    fontWeight: '700',
                                    padding: '0.2rem 0.5rem',
                                    borderRadius: '6px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.25rem'
                                  }}
                                  title="Only apply this suggestion if you have actual experience in this technology."
                                >
                                  ⚠️ Verify Experience
                                </span>
                              )}
                            </div>
                            
                            <p style={{ fontSize: '0.85rem', lineHeight: '1.45', color: 'var(--text-primary)' }}>
                              {sug.explanation}
                            </p>
                            
                            {sug.example_rewrite && (
                              <div style={{
                                background: 'rgba(9, 13, 22, 0.3)',
                                borderLeft: '3px solid var(--accent-color)',
                                borderRadius: '0 8px 8px 0',
                                padding: '0.75rem',
                                fontSize: '0.8rem',
                                fontFamily: 'var(--font-body)'
                              }}>
                                <strong style={{ color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                  💡 Suggested Formatting / Rewrite:
                                </strong>
                                <div style={{ color: '#c7d2fe', whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                                  {sug.example_rewrite}
                                </div>
                              </div>
                            )}
                            
                            {sug.requires_verification && sug.unverified_skills && sug.unverified_skills.length > 0 && (
                              <div style={{
                                background: 'rgba(244, 63, 94, 0.04)',
                                border: '1px dashed rgba(244, 63, 94, 0.25)',
                                borderRadius: '8px',
                                padding: '0.5rem 0.75rem',
                                fontSize: '0.75rem',
                                color: '#fda4af',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.15rem'
                              }}>
                                <strong>⚠️ Anti-Hallucination Warning:</strong>
                                <span>
                                  This suggestion introduces skills/tools not found in your original resume text: <strong>{sug.unverified_skills.join(', ')}</strong>. Do not use this rewrite if you do not possess these skills.
                                </span>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ) : (
                /* Tab 3: ATS Formatting Checklist */
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem', paddingBottom: '1.25rem', borderBottom: '1px solid var(--border-color)' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-secondary)' }}>Overall ATS Match</h3>
                    
                    {/* Score circle */}
                    <div 
                      className={`score-radial-wrapper ${getScoreColorClass(result.ats.score)}`}
                      style={{
                        width: '130px',
                        height: '130px',
                        borderRadius: '50%',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center',
                        position: 'relative',
                        boxShadow: '0 10px 25px rgba(0,0,0,0.4)'
                      }}
                    >
                      <span style={{ fontSize: '2.5rem', fontWeight: '800', fontFamily: 'var(--font-heading)' }}>
                        {result.ats.score}
                      </span>
                      <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1px', opacity: 0.8 }}>
                        Out of 100
                      </span>
                    </div>
                    
                    <p style={{ 
                      fontSize: '0.9rem', 
                      textAlign: 'center', 
                      fontWeight: '600',
                      color: result.ats.score >= 75 ? 'var(--success)' : result.ats.score >= 50 ? 'var(--warning)' : 'var(--error)'
                    }}>
                      {result.ats.score >= 75 ? 'Excellent Compatibility!' : result.ats.score >= 50 ? 'Needs Improvement' : 'Critical Formatting Gaps'}
                    </p>
                  </div>

                  {/* Accordion detail points */}
                  <div>
                    <h4 className="form-label" style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>Scoring Categories</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {Object.entries(result.ats.details).map(([key, value]) => {
                        const hasIssues = value.feedback.length > 0;
                        return (
                          <div 
                            key={key} 
                            style={{
                              background: 'rgba(255,255,255,0.02)',
                              border: '1px solid var(--border-color)',
                              borderRadius: '10px',
                              padding: '0.6rem 0.8rem'
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontWeight: '700', textTransform: 'capitalize', fontSize: '0.8rem' }}>
                                {key === 'contact' ? 'Contact Info' : key === 'dates' ? 'Date Formatting' : key === 'layout' ? 'Layout Complexity' : key === 'headings' ? 'Section Headings' : key}
                              </span>
                              <span style={{ 
                                fontSize: '0.8rem', 
                                fontWeight: '600',
                                color: !hasIssues ? 'var(--success)' : 'var(--text-muted)'
                              }}>
                                {value.score} / {value.max}
                              </span>
                            </div>
                            {hasIssues && (
                              <div style={{ 
                                marginTop: '0.4rem', 
                                paddingTop: '0.4rem',
                                borderTop: '1px solid rgba(255,255,255,0.04)',
                                fontSize: '0.75rem',
                                color: 'var(--text-secondary)',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.2rem'
                              }}>
                                {value.feedback.map((f, idx) => (
                                  <div key={idx} style={{ display: 'flex', gap: '0.3rem' }}>
                                    <span style={{ color: 'var(--error)' }}>•</span>
                                    <span>{f}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Action recommendations list */}
                  {result.ats.feedback_list.length > 0 && (
                    <div style={{ paddingTop: '0.75rem', borderTop: '1px solid var(--border-color)' }}>
                      <h4 className="form-label" style={{ marginBottom: '0.5rem', color: 'var(--error)', fontSize: '0.85rem' }}>
                        Action Items to Fix
                      </h4>
                      <ul style={{ 
                        listStyle: 'none', 
                        display: 'flex', 
                        flexDirection: 'column', 
                        gap: '0.35rem', 
                        fontSize: '0.8rem',
                        color: 'var(--text-secondary)'
                      }}>
                        {result.ats.feedback_list.map((fb, idx) => (
                          <li key={idx} style={{ display: 'flex', gap: '0.35rem' }}>
                            <span>❌</span>
                            <span>{fb}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Contextual Next Step Prompt */}
                  <div style={{ marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end' }}>
                    <button
                      onClick={() => navigate('/interviews')}
                      className="submit-btn"
                      style={{ width: 'auto', padding: '0 1.25rem', height: '42px', fontSize: '0.9rem' }}
                    >
                      Generate Prep Plan & Mock Practice ➔
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Resume;
