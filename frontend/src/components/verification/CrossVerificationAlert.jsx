import React, { useState, useEffect } from 'react';
import { AlertTriangle, X, CheckCircle } from 'lucide-react';
import './CrossVerificationAlert.css';

const DOCUMENT_LABELS = {
  aadhar: 'Aadhar',
  ssc: 'SSC',
  inter: 'Inter',
  rank: 'Rank'
};

const STORAGE_KEY = 'dismissed_name_mismatches';

const getDismissedMismatches = () => {
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
};

const setDismissedMismatches = (appId) => {
  try {
    const dismissed = getDismissedMismatches();
    if (!dismissed.includes(appId)) {
      dismissed.push(appId);
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(dismissed));
    }
  } catch {
    // Ignore storage errors
  }
};

export const CrossVerificationAlert = ({ applicationId, crossVerification }) => {
  const [isDismissed, setIsDismissed] = useState(false);

  useEffect(() => {
    if (applicationId) {
      const dismissed = getDismissedMismatches();
      setIsDismissed(dismissed.includes(applicationId));
    }
  }, [applicationId]);

  if (!crossVerification || !crossVerification.name_consistent) {
    return null;
  }

  if (isDismissed) {
    return null;
  }

  const { name_details, mismatches } = crossVerification;
  const mismatchDocs = mismatches || [];

  const handleDismiss = () => {
    setIsDismissed(true);
    if (applicationId) {
      setDismissedMismatches(applicationId);
    }
  };

  const isMismatch = (docType) => {
    return mismatchDocs.some(m => 
      m?.toLowerCase() === docType?.toLowerCase()
    );
  };

  return (
    <div className="cross-verification-alert">
      <div className="alert-header">
        <AlertTriangle size={18} className="alert-icon" />
        <span className="alert-title">Name Mismatch Across Documents</span>
        <button className="dismiss-btn" onClick={handleDismiss}>
          <X size={16} />
          Dismiss
        </button>
      </div>

      <div className="name-comparison">
        {Object.entries(name_details || {}).map(([docType, name]) => {
          const hasMismatch = isMismatch(docType);
          return (
            <div 
              key={docType} 
              className={`name-row ${hasMismatch ? 'mismatch' : ''}`}
            >
              <span className="doc-label">
                {DOCUMENT_LABELS[docType?.toLowerCase()] || docType}:
              </span>
              <span className="doc-name">{name || 'Not available'}</span>
              {hasMismatch && (
                <span className="mismatch-badge">
                  <AlertTriangle size={12} />
                  Mismatch
                </span>
              )}
              {!hasMismatch && name && (
                <CheckCircle size={14} className="match-icon" />
              )}
            </div>
          );
        })}
      </div>

      <p className="alert-message">
        Please verify the correct name with the student.
      </p>
    </div>
  );
};

export default CrossVerificationAlert;
