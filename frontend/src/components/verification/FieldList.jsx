import React, { useState } from 'react';
import {
  CheckCircle,
  AlertCircle,
  Edit3,
  Check,
  Undo2,
  Flag,
  Circle,
  Upload
} from 'lucide-react';
import './FieldList.css';

// Utility to get confidence color
const getConfidenceColor = (score) => {
  if (score >= 0.90) return 'success';
  if (score >= 0.70) return 'warning';
  return 'danger';
};

// Format field name for display
const formatFieldName = (name) => {
  return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
};

// FieldRow component - individual field display
const FieldRow = ({
  fieldName,
  value,
  confidence,
  state,
  onApprove,
  onEdit,
  onSave,
  onUndo,
  isEditing,
  editValue,
  onEditChange,
  onEditNotesChange,
  editNotes,
  isPending
}) => {
  const confidenceColor = getConfidenceColor(confidence);
  const confidencePercent = Math.round(confidence * 100);

  const handleUndo = () => {
    onUndo(fieldName, value);
  };

  return (
    <div className={`field-row ${state} ${isEditing ? 'editing' : ''}`}>
      <div className="field-header">
        <span className="field-name">{formatFieldName(fieldName)}</span>
        <div className="field-confidence">
          <span className={`confidence-indicator ${confidenceColor}`}>
            {confidenceColor === 'success' ? '●●●' : confidenceColor === 'warning' ? '●●○' : '●○○'}
          </span>
          <span className={`confidence-value ${confidenceColor}`}>{confidencePercent}%</span>
        </div>
      </div>

      {isEditing ? (
        <div className="field-edit-form">
          <textarea
            value={editValue}
            onChange={(e) => onEditChange(e.target.value)}
            rows={2}
            className="edit-textarea"
            autoFocus
          />
          <input
            type="text"
            placeholder="Notes (optional)"
            value={editNotes}
            onChange={(e) => onEditNotesChange(e.target.value)}
            className="edit-notes"
          />
          <div className="edit-actions">
            <button
              className="btn-save"
              onClick={() => onSave(fieldName, editValue, editNotes)}
            >
              <Check size={14} />
              Save
            </button>
            <button
              className="btn-cancel"
              onClick={() => onEdit(null)}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="field-value-row">
          <div className="field-value-content">
            {state === 'edited' && (
              <div className="value-comparison">
                <span className="original-value">
                  <span className="label">Original:</span> {value}
                </span>
                <span className="arrow">→</span>
              </div>
            )}
            <span className={`field-value ${state}`}>{value || '-'}</span>
          </div>

          <div className="field-actions">
            {state === 'pending' && (
              <>
                <button
                  className="action-btn approve"
                  onClick={() => onApprove(fieldName)}
                  title="Approve"
                >
                  <CheckCircle size={16} />
                </button>
                <button
                  className="action-btn edit"
                  onClick={() => onEdit(fieldName, value)}
                  title="Edit"
                >
                  <Edit3 size={16} />
                </button>
              </>
            )}
            {(state === 'approved' || state === 'edited') && (
              <button
                className="action-btn undo"
                onClick={handleUndo}
                title="Undo - revert to original"
              >
                <Undo2 size={16} />
              </button>
            )}
            {state === 'flagged' && (
              <button
                className="action-btn unflag"
                onClick={() => onApprove(fieldName)}
                title="Unflag"
              >
                <Flag size={16} />
              </button>
            )}
          </div>
        </div>
      )}

      {state !== 'pending' && (
        <div className="field-state-badge">
          {state === 'approved' && <><CheckCircle size={12} /> Approved</>}
          {state === 'edited' && <><Edit3 size={12} /> Edited</>}
          {state === 'flagged' && <><Flag size={12} /> Flagged</>}
        </div>
      )}
    </div>
  );
};

// Main FieldList component
export const FieldList = ({
  documentLabel,
  fields = {},
  confidenceScores = {},
  fieldStates = {},
  onApproveField,
  onEditField,
  onApproveAll,
  isApproving,
  isEditing,
  editingField,
  editValue,
  editNotes,
  onEditStart,
  onEditCancel,
  onEditChange,
  onEditNotesChange,
  onEditSave,
  rejectedDocuments = [],
  onViewRejectedDetails
}) => {
  const fieldEntries = Object.entries(fields);
  const pendingFields = fieldEntries.filter(([name]) => fieldStates[name] === 'pending');
  const pendingCount = pendingFields.length;
  const totalCount = fieldEntries.length;
  const rejectedCount = rejectedDocuments.length;

  return (
    <div className="field-list">
      {/* Rejection Banner */}
      {rejectedCount > 0 && (
        <div className="rejection-banner">
          <div className="rejection-banner-content">
            <Upload size={18} className="rejection-icon" />
            <div className="rejection-text">
              <span className="rejection-count">{rejectedCount} document{rejectedCount > 1 ? 's' : ''} awaiting re-upload from student.</span>
              <span className="rejection-hint">Application will return to queue when re-uploaded.</span>
            </div>
          </div>
          {onViewRejectedDetails && (
            <button className="view-details-btn" onClick={onViewRejectedDetails}>
              View Details
            </button>
          )}
        </div>
      )}

      {/* Header */}
      <div className="field-list-header">
        <h3>{documentLabel} — Fields ({totalCount})</h3>
        {pendingCount > 0 ? (
          <button
            className="approve-all-btn"
            onClick={onApproveAll}
            disabled={isApproving || pendingCount === 0}
          >
            <CheckCircle size={16} />
            Approve All Pending ({pendingCount})
          </button>
        ) : (
          <span className="all-approved-badge">
            <CheckCircle size={16} /> All Approved
          </span>
        )}
      </div>

      {/* Fields List */}
      <div className="fields-container">
        {fieldEntries.length === 0 ? (
          <div className="no-fields">
            <AlertCircle size={24} />
            <p>No fields extracted from this document</p>
          </div>
        ) : (
          fieldEntries.map(([fieldName, value]) => (
            <FieldRow
              key={fieldName}
              fieldName={fieldName}
              value={value}
              confidence={confidenceScores[fieldName] || 0}
              state={fieldStates[fieldName] || 'pending'}
              onApprove={onApproveField}
              onEdit={onEditStart}
              onSave={onEditSave}
              onUndo={onEditField}
              isEditing={editingField === fieldName}
              editValue={editingField === fieldName ? editValue : value}
              editNotes={editingField === fieldName ? editNotes : ''}
              onEditChange={onEditChange}
              onEditNotesChange={onEditNotesChange}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default FieldList;