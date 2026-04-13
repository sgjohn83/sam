import React, { useEffect, useCallback } from 'react';
import { CheckCircle, AlertCircle, XCircle, Clock } from 'lucide-react';
import './DocumentTabs.css';

const DOCUMENT_LABELS = ['Aadhar', 'SSC', 'Inter', 'Rank'];

const getStatusIcon = (status) => {
  switch (status) {
    case 'verified':
      return <CheckCircle size={16} className="doc-status-icon verified" />;
    case 'rejected':
      return <XCircle size={16} className="doc-status-icon rejected" />;
    case 'in_progress':
      return <Clock size={16} className="doc-status-icon in-progress" />;
    default:
      return <AlertCircle size={16} className="doc-status-icon" />;
  }
};

const getConfidenceColor = (score) => {
  if (score >= 0.90) return 'success';
  if (score >= 0.70) return 'warning';
  return 'danger';
};

export const DocumentTabs = ({
  documents,
  activeIndex,
  onTabChange,
  hasUnsavedChanges,
  onConfirmSwitch
}) => {
  const handleTabClick = useCallback((index) => {
    if (hasUnsavedChanges && index !== activeIndex) {
      const confirmed = window.confirm(
        'You have unsaved changes. Are you sure you want to switch documents?'
      );
      if (confirmed) {
        onConfirmSwitch?.();
        onTabChange(index);
      }
      return;
    }
    onTabChange(index);
  }, [activeIndex, hasUnsavedChanges, onTabChange, onConfirmSwitch]);

  const handleKeyDown = useCallback((e) => {
    const key = parseInt(e.key, 10);
    if (key >= 1 && key <= 4) {
      const targetIndex = key - 1;
      if (targetIndex < documents.length) {
        handleTabClick(targetIndex);
      }
    }
  }, [documents.length, handleTabClick]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const getDocumentStatus = (doc) => {
    if (doc.status === 'verified') return 'verified';
    if (doc.status === 'rejected') return 'rejected';
    
    const fieldStates = doc.ocr_result?.field_states || {};
    const totalFields = Object.keys(fieldStates).length;
    const reviewedFields = Object.values(fieldStates).filter(
      (state) => state === 'approved' || state === 'edited'
    ).length;

    if (totalFields === 0) return 'not_started';
    if (reviewedFields > 0 && reviewedFields < totalFields) return 'in_progress';
    if (reviewedFields === 0) return 'not_started';
    
    return 'not_started';
  };

  const getProgressText = (doc) => {
    const fieldStates = doc.ocr_result?.field_states || {};
    const totalFields = Object.keys(fieldStates).length;
    const reviewedFields = Object.values(fieldStates).filter(
      (state) => state === 'approved' || state === 'edited'
    ).length;

    if (totalFields === 0) return null;
    return `${reviewedFields}/${totalFields}`;
  };

  return (
    <div className="document-tabs">
      {documents.map((doc, idx) => {
        const status = getDocumentStatus(doc);
        const progressText = getProgressText(doc);
        const confidenceScore = doc.ocr_result?.confidence_scores?.[doc.document_type] || 0;
        
        return (
          <button
            key={doc.id || idx}
            className={`doc-tab ${status} ${idx === activeIndex ? 'active' : ''}`}
            onClick={() => handleTabClick(idx)}
            title={`Press [${idx + 1}] to switch`}
          >
            {getStatusIcon(status)}
            <span className="doc-tab-name">
              {DOCUMENT_LABELS[idx] || doc.document_label || `Doc ${idx + 1}`}
              {progressText && status === 'in_progress' && (
                <span className="doc-progress">{progressText}</span>
              )}
            </span>
            <span className={`doc-confidence-badge ${getConfidenceColor(confidenceScore)}`}>
              {Math.round(confidenceScore * 100)}%
            </span>
          </button>
        );
      })}
      <div className="keyboard-hint">
        <span>1-4</span>
      </div>
    </div>
  );
};

export default DocumentTabs;
