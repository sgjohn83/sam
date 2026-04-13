import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { X, AlertTriangle, Mail, FileText, Image, Clock, AlertCircle, Eye, HelpCircle } from 'lucide-react';
import './RejectDocumentModal.css';

const rejectionSchema = z.object({
  rejection_category: z.enum([
    'blurry', 'wrong_document', 'incomplete', 'expired', 'mismatch', 'unreadable', 'other'
  ], { required_error: 'Please select a category' }),
  rejection_reason: z
    .string()
    .min(10, 'Reason must be at least 10 characters')
    .max(1000, 'Reason must not exceed 1000 characters'),
  notify_student: z.boolean().default(true),
});

const CATEGORY_OPTIONS = [
  { value: 'blurry', label: 'Blurry Image', icon: Eye, description: 'Image is not clear or readable' },
  { value: 'wrong_document', label: 'Wrong Document', icon: FileText, description: 'This is not the requested document' },
  { value: 'incomplete', label: 'Incomplete Document', icon: HelpCircle, description: 'Partial document, missing pages' },
  { value: 'expired', label: 'Expired Document', icon: Clock, description: 'Document has expired' },
  { value: 'mismatch', label: 'Data Mismatch', icon: AlertTriangle, description: 'Data does not match other documents' },
  { value: 'unreadable', label: 'Unreadable', icon: AlertCircle, description: 'Cannot process this document' },
  { value: 'other', label: 'Other', icon: HelpCircle, description: 'Other issue not listed' },
];

export function RejectDocumentModal({ isOpen, onClose, documentLabel, onSubmit, isSubmitting }) {
  const [showPreview, setShowPreview] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isValid },
  } = useForm({
    resolver: zodResolver(rejectionSchema),
    mode: 'onChange',
    defaultValues: {
      rejection_category: '',
      rejection_reason: '',
      notify_student: true,
    },
  });

  const watchedCategory = watch('rejection_category');
  const watchedReason = watch('rejection_reason');
  const watchedNotify = watch('notify_student');

  const selectedCategory = CATEGORY_OPTIONS.find(c => c.value === watchedCategory);
  const charCount = watchedReason?.length || 0;

  const handleFormSubmit = (data) => {
    onSubmit(data);
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Reject Document</h3>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit(handleFormSubmit)}>
          <div className="form-group">
            <label className="form-label">Category *</label>
            <div className="category-grid">
              {CATEGORY_OPTIONS.map(({ value, label, icon: Icon, description }) => (
                <label
                  key={value}
                  className={`category-option ${watchedCategory === value ? 'selected' : ''}`}
                >
                  <input
                    type="radio"
                    value={value}
                    {...register('rejection_category')}
                  />
                  <Icon size={18} />
                  <span className="category-label">{label}</span>
                </label>
              ))}
            </div>
            {errors.rejection_category && (
              <span className="error-text">{errors.rejection_category.message}</span>
            )}
          </div>

          <div className="form-group">
            <label className="form-label">Reason *</label>
            <textarea
              className="form-textarea"
              placeholder="Explain why this document is being rejected..."
              {...register('rejection_reason')}
              rows={4}
            />
            <div className="char-counter">
              <span className={charCount < 10 ? 'error-text' : charCount > 1000 ? 'error-text' : ''}>
                {charCount}/1000
              </span>
              {charCount < 10 && charCount > 0 && (
                <span className="hint-text">Minimum 10 characters required</span>
              )}
            </div>
            {errors.rejection_reason && (
              <span className="error-text">{errors.rejection_reason.message}</span>
            )}
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input type="checkbox" {...register('notify_student')} />
              <Mail size={16} />
              <span>Notify student by email</span>
            </label>
          </div>

          <div className="preview-section">
            <button
              type="button"
              className="preview-toggle"
              onClick={() => setShowPreview(!showPreview)}
            >
              {showPreview ? 'Hide Preview' : 'Show Preview'}
            </button>
            
            {showPreview && (
              <div className="preview-card">
                <div className="preview-header">Email Preview</div>
                <div className="preview-subject">Document Re-upload Required</div>
                <div className="preview-body">
                  <p><strong>Document:</strong> {documentLabel}</p>
                  <p><strong>Issue:</strong> {selectedCategory?.label || 'Not selected'}</p>
                  <p><strong>Reason:</strong> {watchedReason || 'No reason provided'}</p>
                </div>
                {watchedNotify && (
                  <div className="preview-notice">
                    <Mail size={14} />
                    <span>Student will receive this notification via email</span>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-cancel" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn-reject"
              disabled={!isValid || isSubmitting}
            >
              {isSubmitting ? 'Rejecting...' : 'Reject & Notify'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default RejectDocumentModal;