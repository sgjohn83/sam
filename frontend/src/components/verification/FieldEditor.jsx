import React, { useState, useEffect } from 'react';
import {
  X,
  Save,
  Edit3,
  AlertCircle
} from 'lucide-react';
import './FieldEditor.css';

// Large fields that should open in modal
const LARGE_FIELDS = ['address', 'subjects', 'subject_results', 'subjects_list', 'transcript', 'raw_text'];

// Check if field is a "large" field that needs modal
const isLargeField = (fieldName) => {
  const lower = fieldName.toLowerCase();
  return LARGE_FIELDS.some(f => lower.includes(f));
};

export const FieldEditor = ({
  fieldName,
  originalValue,
  currentValue,
  isEditing,
  onStartEdit,
  onSave,
  onCancel,
  isSaving
}) => {
  const [editValue, setEditValue] = useState(currentValue || '');
  const [notes, setNotes] = useState('');
  const [showModal, setShowModal] = useState(false);

  const isLarge = isLargeField(fieldName);
  const displayValue = editValue || currentValue || '-';

  // Reset edit value when entering edit mode
  useEffect(() => {
    if (isEditing) {
      setEditValue(currentValue || '');
      setNotes('');
      // For large fields, show modal
      if (isLarge) {
        setShowModal(true);
      }
    } else {
      setShowModal(false);
    }
  }, [isEditing, currentValue, isLarge]);

  const handleSave = () => {
    onSave(fieldName, editValue, notes);
    setShowModal(false);
  };

  const handleCancel = () => {
    setEditValue(currentValue || '');
    setNotes('');
    setShowModal(false);
    onCancel();
  };

  const handleStartEdit = () => {
    onStartEdit(fieldName, currentValue);
  };

  // If not editing, show view mode
  if (!isEditing) {
    return (
      <div className="field-editor-view">
        <span className="field-value">{displayValue}</span>
        <button
          className="edit-trigger-btn"
          onClick={handleStartEdit}
          title="Edit field"
        >
          <Edit3 size={14} />
        </button>
      </div>
    );
  }

  // Modal for large fields
  if (showModal) {
    return (
      <>
        <div className="field-editor-inline">
          <div className="original-value-display">
            <span className="label">Original:</span>
            <span className="value">{originalValue || '-'}</span>
          </div>
          <textarea
            className="edit-textarea"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            rows={4}
            autoFocus
            disabled={isSaving}
          />
          <input
            type="text"
            className="edit-notes-input"
            placeholder="Notes (optional) - e.g., 'Removed spaces for consistency'"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={isSaving}
          />
          <div className="edit-actions">
            <button
              className="btn-save"
              onClick={handleSave}
              disabled={isSaving || editValue === currentValue}
            >
              <Save size={14} />
              {isSaving ? 'Saving...' : 'Save'}
            </button>
            <button
              className="btn-cancel"
              onClick={handleCancel}
              disabled={isSaving}
            >
              <X size={14} />
              Cancel
            </button>
          </div>
        </div>

        {/* Modal Overlay */}
        {showModal && (
          <div className="field-editor-modal-overlay" onClick={handleCancel}>
            <div className="field-editor-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>Edit: {formatFieldName(fieldName)}</h3>
                <button className="modal-close" onClick={handleCancel}>
                  <X size={20} />
                </button>
              </div>

              <div className="modal-body">
                <div className="original-value-box">
                  <span className="label">Original Value:</span>
                  <p>{originalValue || '-'}</p>
                </div>

                <div className="edit-field-group">
                  <label>New Value:</label>
                  <textarea
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    rows={6}
                    disabled={isSaving}
                    autoFocus
                  />
                </div>

                <div className="edit-notes-group">
                  <label>Notes (optional):</label>
                  <input
                    type="text"
                    placeholder="Reason for edit - e.g., 'Removed spaces for consistency'"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    disabled={isSaving}
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button
                  className="btn-save"
                  onClick={handleSave}
                  disabled={isSaving || editValue === currentValue}
                >
                  <Save size={16} />
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  className="btn-cancel"
                  onClick={handleCancel}
                  disabled={isSaving}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  // Inline edit for regular fields
  return (
    <div className="field-editor-inline">
      <div className="original-value-display">
        <span className="label">Original:</span>
        <span className="value">{originalValue || '-'}</span>
      </div>
      <input
        type="text"
        className="edit-input"
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        disabled={isSaving}
        autoFocus
      />
      <input
        type="text"
        className="edit-notes-input"
        placeholder="Notes (optional)"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        disabled={isSaving}
      />
      <div className="edit-actions">
        <button
          className="btn-save"
          onClick={handleSave}
          disabled={isSaving || editValue === currentValue}
        >
          <Save size={14} />
          {isSaving ? '...' : 'Save'}
        </button>
        <button
          className="btn-cancel"
          onClick={handleCancel}
          disabled={isSaving}
        >
          <X size={14} />
          Cancel
        </button>
      </div>
    </div>
  );
};

// Helper to format field name
const formatFieldName = (name) => {
  return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
};

export default FieldEditor;