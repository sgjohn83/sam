import React from 'react';
import { CheckCircle, Clock, XCircle, AlertCircle, Lock } from 'lucide-react';
import './ProgressSummary.css';

const DOCUMENT_LABELS = {
  aadhar: 'Aadhar Card',
  ssc: '10th Marksheet',
  inter: '12th Marksheet',
  rank: 'Rank Card'
};

const getDocumentLabel = (docType) => {
  return DOCUMENT_LABELS[docType?.toLowerCase()] || docType || 'Document';
};

const getStatusIcon = (status) => {
  switch (status) {
    case 'verified':
      return <CheckCircle size={16} className="status-icon verified" />;
    case 'rejected':
      return <XCircle size={16} className="status-icon rejected" />;
    case 'in_progress':
      return <Clock size={16} className="status-icon in-progress" />;
    default:
      return <AlertCircle size={16} className="status-icon not-started" />;
  }
};

export const ProgressSummary = ({
  documents,
  verifiedCount,
  onLockApplication,
  isLocking
}) => {
  const totalDocuments = documents.length;
  const allVerified = verifiedCount === totalDocuments && totalDocuments > 0;

  const getDocumentProgress = (doc) => {
    const fieldStates = doc.ocr_result?.field_states || {};
    const totalFields = Object.keys(fieldStates).length;
    const reviewedFields = Object.values(fieldStates).filter(
      (state) => state === 'approved' || state === 'edited'
    ).length;

    if (doc.status === 'verified') {
      return { text: 'Verified', status: 'verified' };
    }
    if (doc.status === 'rejected') {
      return { text: 'Rejected', status: 'rejected' };
    }
    if (totalFields === 0) {
      return { text: 'Not started', status: 'not_started' };
    }
    if (reviewedFields > 0 && reviewedFields < totalFields) {
      return { text: `${reviewedFields}/${totalFields} fields`, status: 'in_progress' };
    }
    if (reviewedFields === totalFields && totalFields > 0) {
      return { text: 'Ready to verify', status: 'ready' };
    }
    return { text: 'Not started', status: 'not_started' };
  };

  return (
    <div className="progress-summary">
      <div className="progress-header">
        <h3>Verification Progress</h3>
      </div>

      <div className="document-list">
        {documents.map((doc, idx) => {
          const progress = getDocumentProgress(doc);
          return (
            <div key={doc.id || idx} className={`document-item ${progress.status}`}>
              {getStatusIcon(doc.status)}
              <div className="document-info">
                <span className="document-name">
                  {getDocumentLabel(doc.document_type)}
                </span>
                <span className="document-status">{progress.text}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="progress-footer">
        <div className="verified-count">
          {verifiedCount} of {totalDocuments} documents verified
        </div>

        <button
          className="lock-btn"
          onClick={onLockApplication}
          disabled={!allVerified || isLocking}
          title={!allVerified ? "Available after all documents verified (Week 13)" : "Lock application"}
        >
          <Lock size={16} />
          Lock Application
        </button>

        {!allVerified && (
          <p className="lock-hint">
            Lock available after all documents verified (Week 13)
          </p>
        )}
      </div>
    </div>
  );
};

export default ProgressSummary;
