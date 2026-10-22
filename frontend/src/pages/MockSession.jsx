import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const API_URL = 'http://127.0.0.1:8000';

const MockSession = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();

  // State variables
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [isCompleted, setIsCompleted] = useState(false);
  const [questionNumber, setQuestionNumber] = useState(1);
  const [inputMode, setInputMode] = useState('text'); // text or voice
  
  // Text input state
  const [typedAnswer, setTypedAnswer] = useState('');
  
  // Voice recording states
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState('');
  
  // API loading states
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [transcriptionResult, setTranscriptionResult] = useState('');
  const [error, setError] = useState('');

  // Evaluation states
  const [currentEvaluation, setCurrentEvaluation] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [showModelAnswer, setShowModelAnswer] = useState(false);
  const [tempTranscript, setTempTranscript] = useState('');

  // Refs for media recording
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  // Fetch the current/next question on mount
  useEffect(() => {
    fetchNextQuestion();
    return () => clearInterval(timerRef.current);
  }, []);

  // Timer helper for recording duration
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordingSeconds(prev => prev + 1);
      }, 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [isRecording]);

  const fetchNextQuestion = async () => {
    setIsLoading(true);
    setError('');
    setTranscriptionResult('');
    setTypedAnswer('');
    setAudioBlob(null);
    setAudioUrl('');
    setRecordingSeconds(0);
    setCurrentEvaluation(null);
    setShowModelAnswer(false);
    setTempTranscript('');
    
    try {
      const res = await fetch(`${API_URL}/interviews/sessions/${sessionId}/next`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      
      if (res.ok) {
        if (data.completed) {
          setIsCompleted(true);
        } else {
          setCurrentQuestion(data.question);
        }
      } else {
        setError(data.detail || 'Failed to retrieve the next interview question.');
      }
    } catch (err) {
      console.error(err);
      setError('Connection to backend failed.');
    } finally {
      setIsLoading(false);
    }
  };

  // Start voice capture using browser MediaRecorder API
  const startRecording = async () => {
    setError('');
    audioChunksRef.current = [];
    setAudioBlob(null);
    setAudioUrl('');
    setRecordingSeconds(0);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Detect browser-supported format
      const options = { mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg' };
      
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: options.mimeType });
        setAudioBlob(audioBlob);
        setAudioUrl(URL.createObjectURL(audioBlob));
        
        // Stop all audio tracks in stream
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error(err);
      setError('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  // Submit Text or Voice answer to backend
  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!currentQuestion) return;

    setError('');
    setIsSubmitting(true);
    setTempTranscript('');

    try {
      const formData = new FormData();
      formData.append('question_id', currentQuestion.id);
      formData.append('input_type', inputMode);

      if (inputMode === 'text') {
        if (!typedAnswer.trim()) {
          throw new Error('Please type an answer response before submitting.');
        }
        formData.append('answer_text', typedAnswer);
      } else {
        if (!audioBlob) {
          throw new Error('Please record your voice response before submitting.');
        }
        formData.append('file', audioBlob, 'voice_reply.webm');
      }

      const res = await fetch(`${API_URL}/interviews/${sessionId}/answers`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to submit response.');
      }

      if (inputMode === 'voice') {
        setTempTranscript(data.answer_text);
      }

      setIsSubmitting(false);
      setIsEvaluating(true);

      // Trigger AI Answer Evaluation
      const evalRes = await fetch(`${API_URL}/answers/${data.id}/evaluate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const evalData = await evalRes.json();
      if (!evalRes.ok) {
        throw new Error(evalData.detail || 'Failed to evaluate response.');
      }

      setCurrentEvaluation(evalData);
    } catch (err) {
      console.error(err);
      setError(err.message || 'An error occurred during response submission.');
    } finally {
      setIsSubmitting(false);
      setIsEvaluating(false);
    }
  };

  const getDifficultyColor = (diff) => {
    const d = diff.toLowerCase();
    if (d === 'easy') return '#10b981';
    if (d === 'medium') return '#fb541b';
    return '#f43f5e';
  };

  // 1. Completion view
  if (isCompleted) {
    return (
      <div className="dashboard-container" style={{ alignSelf: 'flex-start', margin: '3rem auto', maxWidth: '600px', width: '90%' }}>
        <div className="card" style={{ padding: '3rem 2rem', textAlign: 'center', background: 'rgba(18, 24, 38, 0.6)' }}>
          <span style={{ fontSize: '4.5rem', display: 'block', marginBottom: '1.25rem' }}>🎓</span>
          <h2 className="card-title" style={{ fontSize: '1.75rem', marginBottom: '0.75rem' }}>Mock Session Completed!</h2>
          <p className="card-desc" style={{ marginBottom: '2.25rem', fontSize: '0.95rem' }}>
            Excellent job! You have answered all 9 preparation questions. Your answers and voice transcripts have been safely persisted to your profile.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <button
              onClick={() => navigate('/dashboard')}
              className="submit-btn"
              style={{ width: '100%', height: '46px', fontSize: '0.95rem', background: 'var(--accent-gradient)' }}
            >
              Check Progress Dashboard ➔
            </button>
            <button
              onClick={() => navigate('/study-plan')}
              className="submit-btn"
              style={{
                width: '100%',
                height: '42px',
                fontSize: '0.9rem',
                background: 'none',
                border: '1px solid var(--border-color)',
                color: 'var(--text-secondary)'
              }}
            >
              View Personalized Study Plan
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 2. Loading view
  if (isLoading) {
    return (
      <div className="dashboard-container" style={{ alignSelf: 'flex-start', margin: '3rem auto', maxWidth: '750px', width: '90%' }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '350px' }}>
          <div className="spinner" style={{ width: '45px', height: '45px', borderThickness: '4px', marginBottom: '1.25rem' }}></div>
          <p style={{ color: 'var(--text-secondary)' }}>Serving next mock question...</p>
        </div>
      </div>
    );
  }

  // 3. Question answering view
  return (
    <div className="dashboard-container" style={{ alignSelf: 'flex-start', margin: '2rem auto', maxWidth: '750px', width: '90%' }}>
      <div className="page-header" style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title" style={{ fontSize: '1.4rem' }}>Interview Simulator</h1>
          <p className="page-subtitle" style={{ fontSize: '0.85rem' }}>Answering under simulated conditions</p>
        </div>
        <span style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--text-secondary)', background: 'rgba(255,255,255,0.05)', padding: '0.4rem 0.8rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          Question {questionNumber} / 9
        </span>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.25rem' }}>
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {currentQuestion && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Question Card */}
          <div className="card" style={{ padding: '1.75rem', background: 'rgba(18, 24, 38, 0.4)', position: 'relative', overflow: 'hidden' }}>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', padding: '0.15rem 0.5rem', borderRadius: '4px', background: 'rgba(99, 102, 241, 0.15)', color: '#a5b4fc' }}>
                {currentQuestion.topic_tag}
              </span>
              <span style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', padding: '0.15rem 0.5rem', borderRadius: '4px', background: `${getDifficultyColor(currentQuestion.difficulty)}20`, color: getDifficultyColor(currentQuestion.difficulty) }}>
                {currentQuestion.difficulty}
              </span>
            </div>
            
            <h3 style={{ fontSize: '1.1rem', lineHeight: '1.6', fontWeight: '600', color: 'white' }}>
              {currentQuestion.question_text}
            </h3>
          </div>

          {isEvaluating ? (
            /* Loader for Answer Evaluation */
            <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
              <div className="spinner" style={{ width: '40px', height: '40px', borderThickness: '4px', marginBottom: '1.25rem' }}></div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: 'white', marginBottom: '0.25rem' }}>AI Mentor Evaluation</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                Scoring your response parameters & formulating guidelines...
              </p>
            </div>
          ) : currentEvaluation ? (
            /* Evaluation Scorecard View */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', background: 'rgba(18, 24, 38, 0.5)' }}>
                
                {/* Overall Score Circle Header */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem', paddingBottom: '1.25rem', borderBottom: '1px solid var(--border-color)' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-secondary)' }}>Response Score</h3>
                  
                  <div 
                    className="score-radial-wrapper"
                    style={{
                      width: '120px',
                      height: '120px',
                      borderRadius: '50%',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'center',
                      alignItems: 'center',
                      background: 'rgba(255,255,255,0.02)',
                      border: `3px solid ${currentEvaluation.overall_score >= 80 ? 'var(--success)' : currentEvaluation.overall_score >= 60 ? 'var(--warning)' : 'var(--error)'}`,
                      boxShadow: '0 10px 25px rgba(0,0,0,0.3)'
                    }}
                  >
                    <span style={{ fontSize: '2.25rem', fontWeight: '800', color: 'white' }}>
                      {currentEvaluation.overall_score}
                    </span>
                    <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                      Rating
                    </span>
                  </div>
                </div>

                {/* Sub-scores metrics block */}
                <div>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                    Evaluation Dimensions
                  </h4>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {[
                      { name: 'Correctness', score: currentEvaluation.correctness_score },
                      { name: 'Relevance', score: currentEvaluation.relevance_score },
                      { name: 'Completeness', score: currentEvaluation.completeness_score },
                      { name: 'Technical Depth', score: currentEvaluation.depth_score },
                      { name: 'Communication', score: currentEvaluation.communication_score }
                    ].map((metric) => (
                      <div key={metric.name}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', fontWeight: '600', marginBottom: '0.25rem' }}>
                          <span style={{ color: 'var(--text-primary)' }}>{metric.name}</span>
                          <span style={{ color: 'var(--text-secondary)' }}>{metric.score} / 5</span>
                        </div>
                        <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                          <div 
                            style={{ 
                              height: '100%', 
                              width: `${metric.score * 20}%`, 
                              background: 'var(--accent-gradient)',
                              borderRadius: '3px'
                            }} 
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Strengths and Gaps lists */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                  
                  {/* Strengths */}
                  <div style={{ background: 'rgba(16, 185, 129, 0.03)', border: '1px solid rgba(16, 185, 129, 0.15)', borderRadius: '8px', padding: '1rem' }}>
                    <h4 style={{ fontSize: '0.8rem', color: 'var(--success)', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '0.25rem', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                      <span>✓</span> Strengths
                    </h4>
                    <ul style={{ listStyle: 'none', paddingLeft: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                      {currentEvaluation.strengths.map((str, idx) => (
                        <li key={idx} style={{ fontSize: '0.8rem', color: 'var(--text-primary)', display: 'flex', gap: '0.3rem' }}>
                          <span style={{ color: 'var(--success)' }}>•</span>
                          <span>{str}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Gaps */}
                  <div style={{ background: 'rgba(244, 63, 94, 0.03)', border: '1px solid rgba(244, 63, 94, 0.15)', borderRadius: '8px', padding: '1rem' }}>
                    <h4 style={{ fontSize: '0.8rem', color: 'var(--error)', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '0.25rem', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                      <span>⚠️</span> Areas to Improve
                    </h4>
                    <ul style={{ listStyle: 'none', paddingLeft: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                      {currentEvaluation.gaps.map((gap, idx) => (
                        <li key={idx} style={{ fontSize: '0.8rem', color: 'var(--text-primary)', display: 'flex', gap: '0.3rem' }}>
                          <span style={{ color: 'var(--error)' }}>•</span>
                          <span>{gap}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                </div>

                {/* Collapsible Model Answer Accordion */}
                <div>
                  <button
                    type="button"
                    onClick={() => setShowModelAnswer(!showModelAnswer)}
                    style={{
                      background: 'rgba(255,255,255,0.02)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '8px',
                      width: '100%',
                      padding: '0.75rem 1rem',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      color: 'white',
                      fontSize: '0.85rem',
                      fontWeight: '700',
                      cursor: 'pointer'
                    }}
                  >
                    <span>💡 Model Answer Guide</span>
                    <span>{showModelAnswer ? '▲' : '▼'}</span>
                  </button>
                  
                  {showModelAnswer && (
                    <div style={{
                      marginTop: '0.5rem',
                      padding: '1rem',
                      background: 'rgba(9, 13, 22, 0.3)',
                      borderLeft: '3px solid var(--accent-color)',
                      borderRadius: '0 8px 8px 0',
                      fontSize: '0.85rem',
                      lineHeight: '1.5',
                      color: '#c7d2fe'
                    }}>
                      {currentEvaluation.model_answer}
                    </div>
                  )}
                </div>

                {/* Revision Topics warning badges */}
                {currentEvaluation.revision_topics && currentEvaluation.revision_topics.length > 0 && (
                  <div>
                    <h4 style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                      Recommended Study Topics:
                    </h4>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      {currentEvaluation.revision_topics.map((topic, idx) => (
                        <span 
                          key={idx}
                          style={{
                            background: 'rgba(245, 158, 11, 0.12)',
                            color: '#fbbf24',
                            border: '1px solid rgba(245, 158, 11, 0.25)',
                            padding: '0.2rem 0.5rem',
                            borderRadius: '6px',
                            fontSize: '0.75rem',
                            fontWeight: '600'
                          }}
                        >
                          ⚠️ {topic}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

              </div>
              
              {/* Action Button: Proceed to next question */}
              <button
                type="button"
                onClick={() => {
                  setQuestionNumber(prev => prev + 1);
                  fetchNextQuestion();
                }}
                className="submit-btn"
                style={{ height: '46px', width: '100%', fontSize: '0.95rem', background: 'var(--accent-gradient)' }}
              >
                Proceed to Next Question ➔
              </button>
            </div>
          ) : (
            /* Answering input block (Original interface) */
            <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              
              {/* Mode Selectors */}
              <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
                <button
                  type="button"
                  className="nav-auth-btn"
                  style={{
                    background: inputMode === 'text' ? 'var(--accent-gradient)' : 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-color)',
                    color: 'white',
                    flex: 1,
                    fontSize: '0.85rem',
                    padding: '0.5rem 0.75rem',
                    cursor: 'pointer'
                  }}
                  disabled={isSubmitting}
                  onClick={() => setInputMode('text')}
                >
                  ⌨️ Type Answer
                </button>
                <button
                  type="button"
                  className="nav-auth-btn"
                  style={{
                    background: inputMode === 'voice' ? 'var(--accent-gradient)' : 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-color)',
                    color: 'white',
                    flex: 1,
                    fontSize: '0.85rem',
                    padding: '0.5rem 0.75rem',
                    cursor: 'pointer'
                  }}
                  disabled={isSubmitting}
                  onClick={() => setInputMode('voice')}
                >
                  🎙️ Speak Answer
                </button>
              </div>

              {/* Answering Block */}
              {inputMode === 'text' ? (
                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div className="form-group">
                    <label className="form-label" style={{ fontWeight: '600', fontSize: '0.8rem' }}>Your Response</label>
                    <textarea
                      className="form-input"
                      rows="6"
                      placeholder="Provide a detailed answer explaining the concepts, your experience, or structural logic..."
                      value={typedAnswer}
                      onChange={(e) => setTypedAnswer(e.target.value)}
                      style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)', color: 'white', fontFamily: 'var(--font-body)', fontSize: '0.9rem', padding: '0.75rem' }}
                      disabled={isSubmitting}
                    />
                  </div>
                  
                  <button
                    type="submit"
                    className="submit-btn"
                    disabled={isSubmitting}
                    style={{ height: '44px', width: '100%', fontSize: '0.9rem' }}
                  >
                    {isSubmitting ? (
                      <>
                        <div className="spinner" style={{ marginRight: '0.5rem' }}></div>
                        <span>Submitting response...</span>
                      </>
                    ) : (
                      <span>Submit Answer</span>
                    )}
                  </button>
                </form>
              ) : (
                /* Voice Recording Block */
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem', padding: '1rem 0' }}>
                  
                  {/* Visualizer / State indicator */}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                    <div 
                      style={{
                        width: '100px',
                        height: '100px',
                        borderRadius: '50%',
                        background: isRecording ? 'rgba(244, 63, 94, 0.1)' : 'rgba(255,255,255,0.02)',
                        border: isRecording ? '3px solid #f43f5e' : '1px solid var(--border-color)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: isRecording ? '0 0 20px rgba(244, 63, 94, 0.3)' : 'none',
                        animation: isRecording ? 'pulse 1.5s infinite ease-in-out' : 'none'
                      }}
                    >
                      <span style={{ fontSize: '2.5rem' }}>{isRecording ? '🎙️' : '🎤'}</span>
                    </div>
                    
                    <span style={{ fontSize: '1.25rem', fontWeight: '800', fontFamily: 'monospace', color: 'white', marginTop: '0.5rem' }}>
                      {formatTime(recordingSeconds)}
                    </span>
                    
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {isRecording ? 'Recording microphone audio...' : audioBlob ? 'Audio captured successfully.' : 'Tap record below to speak your answer.'}
                    </span>
                  </div>

                  {/* Recorder Control Buttons */}
                  <div style={{ display: 'flex', gap: '1rem', width: '100%', justifyContent: 'center' }}>
                    {!isRecording && !audioBlob ? (
                      <button
                        type="button"
                        onClick={startRecording}
                        disabled={isSubmitting}
                        className="submit-btn"
                        style={{ background: '#f43f5e', width: '200px', height: '42px' }}
                      >
                        🔴 Start Recording
                      </button>
                    ) : isRecording ? (
                      <button
                        type="button"
                        onClick={stopRecording}
                        className="submit-btn"
                        style={{ background: 'var(--text-secondary)', width: '200px', height: '42px' }}
                      >
                        ⏹️ Stop Recording
                      </button>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem', width: '100%' }}>
                        <audio src={audioUrl} controls style={{ width: '80%', maxWidth: '400px' }} />
                        
                        <div style={{ display: 'flex', gap: '0.75rem' }}>
                          <button
                            type="button"
                            onClick={startRecording}
                            disabled={isSubmitting}
                            style={{
                              background: 'rgba(255,255,255,0.05)',
                              border: '1px solid var(--border-color)',
                              color: 'white',
                              padding: '0.5rem 1rem',
                              borderRadius: '8px',
                              cursor: 'pointer',
                              fontSize: '0.85rem'
                            }}
                          >
                            🔄 Re-record
                          </button>
                          <button
                            type="button"
                            onClick={() => handleSubmit()}
                            disabled={isSubmitting}
                            className="submit-btn"
                            style={{ width: '160px', height: '38px', fontSize: '0.85rem' }}
                          >
                            {isSubmitting ? 'Submitting...' : '📤 Submit & Evaluate'}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Transcribing / Submitting loader panel */}
                  {isSubmitting && (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', width: '80%', padding: '1rem', background: 'rgba(255,255,255,0.02)', border: '1px dashed var(--border-color)', borderRadius: '10px', marginTop: '1rem' }}>
                      <div className="spinner" style={{ width: '24px', height: '24px' }}></div>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        AI speech-to-text transcriber is parsing your response...
                      </span>
                    </div>
                  )}

                  {/* Transcription result preview panel */}
                  {tempTranscript && (
                    <div style={{ width: '90%', padding: '1rem', background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.15)', borderRadius: '10px', marginTop: '1rem' }}>
                      <strong style={{ color: 'var(--success)', display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.25rem' }}>
                        ✓ Generated Transcript:
                      </strong>
                      <p style={{ fontSize: '0.85rem', color: 'white', fontStyle: 'italic', lineHeight: '1.4' }}>
                        "{tempTranscript}"
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MockSession;
