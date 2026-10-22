import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const JOB_ROLES = [
  'Frontend Developer',
  'Backend Developer',
  'Fullstack Developer',
  'Software Engineer',
  'Data Analyst',
  'Data Scientist',
  'Product Manager',
  'DevOps Engineer'
];

const EXPERIENCE_LEVELS = [
  'Fresher',
  '0–1 years',
  '1–3 years',
  '3–5 years',
  '5+ years'
];

const Profile = () => {
  const { user, updateProfile } = useAuth();

  const [name, setName] = useState(user?.name || '');
  const [targetJobRole, setTargetJobRole] = useState(user?.target_job_role || JOB_ROLES[0]);
  const [experienceLevel, setExperienceLevel] = useState(user?.experience_level || EXPERIENCE_LEVELS[0]);

  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSuccess('');
    setError('');

    if (!name.trim()) {
      setError('Name cannot be blank.');
      return;
    }

    setIsSubmitting(true);
    const result = await updateProfile(name, targetJobRole, experienceLevel);
    setIsSubmitting(false);

    if (result.success) {
      setSuccess('Profile updated successfully!');
      // Dismiss success alert after 3 seconds
      setTimeout(() => setSuccess(''), 3000);
    } else {
      setError(result.error || 'Failed to update profile');
    }
  };

  const firstLetter = name ? name.charAt(0) : 'U';

  return (
    <div className="profile-container" style={{ alignSelf: 'flex-start', margin: '2rem auto' }}>
      <div className="page-header">
        <h1 className="page-title">User Profile</h1>
        <p className="page-subtitle">View and update your career preference settings</p>
      </div>

      {success && (
        <div className="alert alert-success">
          <span style={{ fontSize: '1.15rem' }}>✓</span>
          <span>{success}</span>
        </div>
      )}

      {error && (
        <div className="alert alert-error">
          <span style={{ fontSize: '1.15rem' }}>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      <div className="profile-grid">
        <div className="profile-sidebar">
          <div className="avatar-large">{firstLetter}</div>
          <h3 className="profile-meta-name">{user?.name}</h3>
          <p className="profile-meta-email">{user?.email}</p>
          
          <div className="badge-group">
            <div className="profile-badge">
              <div className="badge-label">Job Role</div>
              <div className="badge-value">{user?.target_job_role}</div>
            </div>
            <div className="profile-badge">
              <div className="badge-label">Experience</div>
              <div className="badge-value">{user?.experience_level}</div>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="auth-title" style={{ textAlign: 'left', marginBottom: '1.5rem', fontSize: '1.5rem' }}>
            Edit Profile Preferences
          </h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="profile-name">Full Name</label>
              <input
                id="profile-name"
                type="text"
                className="form-input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="profile-role">Target Job Role</label>
              <select
                id="profile-role"
                className="form-select"
                value={targetJobRole}
                onChange={(e) => setTargetJobRole(e.target.value)}
                required
              >
                {JOB_ROLES.map((role) => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="profile-experience">Experience Level</label>
              <select
                id="profile-experience"
                className="form-select"
                value={experienceLevel}
                onChange={(e) => setExperienceLevel(e.target.value)}
                required
              >
                {EXPERIENCE_LEVELS.map((level) => (
                  <option key={level} value={level}>{level}</option>
                ))}
              </select>
            </div>

            <button type="submit" className="submit-btn" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <div className="spinner"></div>
                  <span>Saving Changes...</span>
                </>
              ) : (
                <span>Save Profile Details</span>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Profile;
