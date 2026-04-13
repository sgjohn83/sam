import React, { useState } from 'react';
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';
import './DocumentActions.css';

export const DocumentActions = ({
  documentLabel,
  totalFields,
  reviewedFields,
  isVerified,
  isRejected,
  onVerifyDocument,
  onRequestReupload,
  isVerifying
}) => {
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showReuploadModal, setShowReuploadModal] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');

  const pendingCount = totalFields - reviewedFields;
  const canVerify = pendingCount === 0 && !isVerified && !isRejected;

  const handleVerifyClick = () => {
    if (!canVerify) return;
    setShowConfirmModal(true);
  };

  const handleConfirmVerify = async () => {
    setShowConfirmModal(false);
    try {
      await onVerifyDocument();
      toast.success(`${documentLabel} verified. Moving to next document.`);
    } catch (error) {
      toast.error(error.message || 'Failed to verify document');
    }
  };

  const handleReuploadClick = () => {
    setShowReuploadModal(true);
  };

  const handleConfirmReupload = () => {
    setShowReuploadModal(false);
    onRequestReupload?.(rejectionReason);
    setRejectionReason('');
  };

  if (isVerified) {
    return (
      <div className="document-actions verified-actions">
        <div className="verified-badge">
          <CheckCircle size={18} />
          <span>{documentLabel} Verified</span>
        </div>
      </div>
    );
  }

  if (isRejected) {
    return (
      <div className="document-actions rejected-actions">
        <div className="rejected-badge">
          <XCircle size={18} />
          <span>Re-upload Requested</span>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="document-actions">
        <div className="verification-progress">
          <span className="progress-label">Verification Progress:</span>
          <span className={`progress-status ${pendingCount === 0 ? 'complete' : 'pending'}`}>
            {pendingCount === 0 ? (
              <>
                <CheckCircle size={14} />
                All {totalFields} fields reviewed
              </>
            ) : (
              <>
                <AlertTriangle size={14} />
                {pendingCount} of {totalFields} fields pending
              </>
            )}
          </span>
        </div>

        <div className="action-buttons">
          <button
            className="btn-verify"
            onClick={handleVerifyClick}
            disabled={!canVerify || isVerifying}
          >
            <CheckCircle size={18} />
            Verify Document
          </button>
          <button
            className="btn-reupload"
            onClick={handleReuploadClick}
          >
            <XCircle size={18} />
            Request Re-upload
          </button>
        </div>
      </div>

      {/* Verify Confirmation Modal */}
      {showConfirmModal && (
        <div className="modal-overlay" onClick={() => setShowConfirmModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <CheckCircle size={24} className="modal-icon success" />
              <h3>Confirm Verification</h3>
            </div>
            <p>Mark this document as verified?</p>
            <p className="modal-subtitle">
              This will lock all fields and mark {documentLabel} as verified.
            </p>
            <div className="modal-actions">
              <button
                className="btn-cancel"
                onClick={() => setShowConfirmModal(false)}
              >
                Cancel
              </button>
              <button
                className="btn-confirm"
                onClick={handleConfirmVerify}
              >
                Verify Document
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Re-upload Request Modal (Placeholder for Week 12) */}
      {showReuploadModal && (
        <div className="modal-overlay" onClick={() => setShowReuploadModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <AlertTriangle size={24} className="modal-icon warning" />
              <h3>Request Re-upload</h3>
            </div>
            <p>Request the student to re-upload this document.</p>
            <div className="modal-form">
              <label htmlFor="rejection-reason">Reason for re-upload (optional)</label>
              <textarea
                id="rejection-reason"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Enter reason for re-upload request..."
                rows={3}
              />
            </div>
            <p className="modal-note">
              Full rejection workflow with notification to student will be available in Week 12.
            </p>
            <div className="modal-actions">
              <button
                className="btn-cancel"
                onClick={() => setShowReuploadModal(false)}
              >
                Cancel
              </button>
              <button
                className="btn-reject"
                onClick={handleConfirmReupload}
              >
                Request Re-upload
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DocumentActions;
