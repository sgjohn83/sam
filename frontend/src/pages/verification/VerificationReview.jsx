import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  Edit3,
  Check,
  Flag,
  Lock,
  Unlock,
  History,
  Shield
} from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../../services/api';
import { DocumentViewer } from '../../components/verification/DocumentViewer';
import { FieldList } from '../../components/verification/FieldList';
import { DocumentTimeline } from '../../components/verification/DocumentTimeline';
import { AuditTrailDrawer } from '../../components/verification/AuditTrailDrawer';
import { Modal } from '../../components/ui/Modal';
import './VerificationReview.css';

// API functions
const verificationApi = {
  getSplitScreen: (id) => api.get(`/verification/${id}/split-screen/`),
  editField: (appId, data) => api.patch(`/verification/${appId}/field/`, data),
  approveField: (appId, data) => api.post(`/verification/${appId}/field/approve/`, data),
  approveAllFields: (appId, data) => api.post(`/verification/${appId}/fields/approve-all/`, data),
  verifyDocument: (appId, docId) => api.post(`/verification/${appId}/document/${docId}/verify/`),
  releaseApplication: (id) => api.post(`/verification/queue/${id}/release/`),
  lockApplication: (id) => api.post(`/applications/${id}/lock/`),
  unlockApplication: (id, reason) => api.post(`/applications/${id}/unlock/`, { reason }),
  getAuditLogs: (id) => api.get(`/verification/applications/${id}/audit-logs/`),
};

const getConfidenceColor = (score) => {
  if (score >= 0.90) return 'success';
  if (score >= 0.70) return 'warning';
  return 'danger';
};

const getConfidenceLabel = (score) => {
  if (score >= 0.90) return 'High';
  if (score >= 0.70) return 'Medium';
  return 'Low';
};

export const VerificationReview = () => {
  const { id: appId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // State
  const [timeLeft, setTimeLeft] = useState('');
  const [isTimerRed, setIsTimerRed] = useState(false);
  const [activeDocIndex, setActiveDocIndex] = useState(0);
  const [editingField, setEditingField] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [editNotes, setEditNotes] = useState('');
  const [splitPosition, setSplitPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const [showLockModal, setShowLockModal] = useState(false);
  const [showUnlockModal, setShowUnlockModal] = useState(false);
  const [unlockReason, setUnlockReason] = useState('');
  const [showAuditDrawer, setShowAuditDrawer] = useState(false);

  // Fetch split-screen data
  const { data: splitData, isLoading, isError, error } = useQuery({
    queryKey: ['split-screen', appId],
    queryFn: () => verificationApi.getSplitScreen(appId),
    refetchInterval: 30000,
  });

  // Mutations
  const releaseMutation = useMutation({
    mutationFn: () => verificationApi.releaseApplication(appId),
    onSuccess: () => {
      toast.success('Application released');
      navigate('/verification/queue');
    },
    onError: (err) => {
      toast.error(err.response?.data?.error || 'Failed to release');
    }
  });

  const editFieldMutation = useMutation({
    mutationFn: ({ fieldName, newValue, notes }) =>
      verificationApi.editField(appId, {
        document_id: activeDoc?.id,
        field_name: fieldName,
        new_value: newValue,
        notes
      }),
    onSuccess: () => {
      toast.success('Field updated');
      setEditingField(null);
      queryClient.invalidateQueries(['split-screen', appId]);
    },
    onError: (err) => {
      toast.error(err.response?.data?.error || 'Failed to update field');
    }
  });

  const approveFieldMutation = useMutation({
    mutationFn: ({ fieldName }) =>
      verificationApi.approveField(appId, {
        document_id: activeDoc?.id,
        field_name: fieldName
      }),
    onSuccess: () => {
      toast.success('Field approved');
      queryClient.invalidateQueries(['split-screen', appId]);
    },
    onError: (err) => {
      toast.error(err.response?.data?.error || 'Failed to approve field');
    }
  });

  const approveAllMutation = useMutation({
    mutationFn: () => verificationApi.approveAllFields(appId, {
      document_id: activeDoc?.id
    }),
    onSuccess: (res) => {
      toast.success(`Approved ${res.data.approved_count} fields`);
      queryClient.invalidateQueries(['split-screen', appId]);
    },
    onError: (err) => {
      toast.error(err.response?.data?.error || 'Failed to approve all fields');
    }
  });

  const verifyDocumentMutation = useMutation({
    mutationFn: () => verificationApi.verifyDocument(appId, activeDoc?.id),
    onSuccess: () => {
      toast.success('Document verified!');
      queryClient.invalidateQueries(['split-screen', appId]);
    },
    onError: (err) => {
      toast.error(err.response?.data?.error || 'Failed to verify document');
    }
  });

  const lockMutation = useMutation({
    mutationFn: () => verificationApi.lockApplication(appId),
    onSuccess: () => {
      toast.success('Application locked successfully');
      setShowLockModal(false);
      queryClient.invalidateQueries(['split-screen', appId]);
    },
    onError: (err) => {
      toast.error(err.response?.data?.error || 'Failed to lock application');
    }
  });

  const unlockMutation = useMutation({
    mutationFn: (reason) => verificationApi.unlockApplication(appId, reason),
    onSuccess: () => {
      toast.success('Application unlocked successfully');
      setShowUnlockModal(false);
      setUnlockReason('');
      queryClient.invalidateQueries(['split-screen', appId]);
    },
    onError: (err) => {
      toast.error(err.response?.data?.error || 'Failed to unlock application');
    }
  });

  // Timer logic
  useEffect(() => {
    if (!splitData?.application?.claimed_at) return;

    const calculate = () => {
      const claimDate = new Date(splitData.application.claimed_at);
      const expiry = new Date(claimDate.getTime() + 30 * 60000);
      const diff = expiry - new Date();

      if (diff <= 0) {
        setTimeLeft('Expired');
        setIsTimerRed(true);
        return;
      }

      const mins = Math.floor(diff / 60000);
      const secs = Math.floor((diff % 60000) / 1000);
      setTimeLeft(`${mins}:${secs.toString().padStart(2, '0')}`);
      setIsTimerRed(diff < 5 * 60000); // Red if less than 5 minutes
    };

    calculate();
    const timer = setInterval(calculate, 1000);
    return () => clearInterval(timer);
  }, [splitData?.application?.claimed_at]);

  // Split panel drag handler
  const handleMouseDown = useCallback(() => {
    setIsDragging(true);
  }, []);

  const handleMouseMove = useCallback((e) => {
    if (!isDragging) return;
    const container = document.querySelector('.split-content');
    if (container) {
      const rect = container.getBoundingClientRect();
      const newPosition = ((e.clientX - rect.left) / rect.width) * 100;
      setSplitPosition(Math.min(Math.max(newPosition, 20), 80));
    }
  }, [isDragging]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // Derived data
  const application = splitData?.application;
  const student = splitData?.student;
  const documents = splitData?.documents || [];
  const crossVerification = splitData?.cross_verification;
  const verificationProgress = splitData?.verification_progress;
  const activeDoc = documents[activeDocIndex];
  const ocrResult = activeDoc?.ocr_result;
  const fields = ocrResult?.extracted_fields || {};
  const confidenceScores = ocrResult?.confidence_scores || {};
  const fieldStates = ocrResult?.field_states || {};
  const pendingCount = Object.values(fieldStates).filter(s => s === 'pending').length;
  const rejectedDocuments = documents.filter(d => d.is_rejected);
  const isLocked = application?.is_locked || false;
  const allDocumentsVerified = documents.length > 0 && documents.every(d => d.status === 'verified');
  const canLock = allDocumentsVerified && !isLocked;

  if (isLoading) {
    return (
      <div className="verification-review-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading application...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="verification-review-page">
        <div className="error-container">
          <XCircle size={48} className="text-danger" />
          <h2>Error Loading Application</h2>
          <p>{error?.response?.data?.error || 'The application may have been released or your claim expired.'}</p>
          <Link to="/verification/queue" className="btn btn-primary">
            Back to Queue
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="verification-review-page">
      {/* Top Header Bar */}
      <div className="review-navbar">
        <Link to="/verification/queue" className="back-link">
          <ArrowLeft size={18} />
          Back to Queue
        </Link>
      </div>

      <div className="review-main-card">
        {/* Header with app info */}
        <div className="review-header">
          <div className="student-header">
            <div className="avatar">
              {student?.full_name?.charAt(0) || '?'}
            </div>
            <div className="student-meta">
              <h2>{application?.application_number}</h2>
              <p>{student?.full_name} • {student?.email}</p>
            </div>
          </div>

          <div className="header-stats">
            <div className={`confidence-badge ${getConfidenceColor(verificationProgress?.verified_count / verificationProgress?.total_documents)}`}>
              <span className="confidence-label">Progress</span>
              <span className="confidence-value">
                {verificationProgress?.verified_count || 0}/{verificationProgress?.total_documents || 0}
              </span>
            </div>

            <div className={`timer-badge ${isTimerRed ? 'timer-red' : ''}`}>
              <Clock size={16} />
              <span>{timeLeft} remaining</span>
            </div>

            <button
              className="release-btn"
              onClick={() => {
                if (window.confirm('Release this application back to the queue?')) {
                  releaseMutation.mutate();
                }
              }}
            >
              Release
            </button>
          </div>
        </div>

        {/* Document Tabs */}
        <div className="document-tabs">
          {documents.map((doc, idx) => {
            const isVerified = doc.status === 'verified';
            return (
              <button
                key={doc.id}
                className={`doc-tab ${idx === activeDocIndex ? 'active' : ''} ${isVerified ? 'verified' : ''}`}
                onClick={() => setActiveDocIndex(idx)}
              >
                {isVerified ? (
                  <CheckCircle size={16} className="doc-status-icon verified" />
                ) : (
                  <AlertCircle size={16} className="doc-status-icon" />
                )}
                <span className="doc-tab-name">{doc.document_label}</span>
                <span className={`doc-confidence-badge ${getConfidenceColor(confidenceScores[doc.document_type])}`}>
                  {Math.round((confidenceScores[doc.document_type] || 0) * 100)}%
                </span>
              </button>
            );
          })}
        </div>

        {/* Document Timeline - shows for documents with multiple uploads */}
        {activeDoc && (
          <DocumentTimeline 
            documentId={activeDoc.id} 
            uploadVersion={activeDoc.upload_version} 
          />
        )}

        {/* Main Split Content */}
        <div className="split-content">
          {/* Left Panel - Document Viewer */}
          <div className="doc-viewer-panel" style={{ width: `${splitPosition}%` }}>
            <DocumentViewer
              documentId={activeDoc?.id}
              fileUrl={activeDoc?.file_url}
              mimeType={activeDoc?.mime_type}
              onLoadError={(err) => {
                console.error('Document load error:', err);
                toast.error('Failed to load document');
              }}
            />
          </div>

          {/* Resizable Divider */}
          <div
            className="split-divider"
            onMouseDown={handleMouseDown}
          >
            <div className="divider-handle"></div>
          </div>

          {/* Right Panel - Extracted Fields */}
          <div className="fields-panel" style={{ width: `${100 - splitPosition}%` }}>
            <div className="fields-header">
              <h3>{activeDoc?.document_label} — Fields</h3>
              {pendingCount > 0 ? (
                <button
                  className="approve-all-btn"
                  onClick={() => approveAllMutation.mutate()}
                  disabled={approveAllMutation.isPending}
                >
                  <CheckCircle size={16} />
                  Approve All ({pendingCount} pending)
                </button>
              ) : (
                <span className="all-approved-badge">
                  <CheckCircle size={16} /> All Approved
                </span>
              )}
            </div>

            <FieldList
              documentLabel={activeDoc?.document_label}
              fields={fields}
              confidenceScores={confidenceScores}
              fieldStates={fieldStates}
              onApproveField={(fieldName) => approveFieldMutation.mutate({ fieldName })}
              onEditField={(fieldName, originalValue) => editFieldMutation.mutate({ fieldName, newValue: originalValue, notes: 'Reverted' })}
              onApproveAll={() => approveAllMutation.mutate()}
              isApproving={approveAllMutation.isPending}
              isEditing={!!editingField}
              editingField={editingField}
              editValue={editValue}
              editNotes={editNotes}
              onEditStart={(f, v) => { setEditingField(f); setEditValue(v); setEditNotes(''); }}
              onEditCancel={() => setEditingField(null)}
              onEditChange={setEditValue}
              onEditNotesChange={setEditNotes}
              onEditSave={(f, v, n) => editFieldMutation.mutate({ fieldName: f, newValue: v, notes: n })}
              rejectedDocuments={rejectedDocuments}
            />

            {/* Document Actions */}
            <div className="document-actions">
              {!isLocked ? (
                <>
                  <button
                    className="btn-verify"
                    onClick={() => verifyDocumentMutation.mutate()}
                    disabled={verifyDocumentMutation.isPending || pendingCount > 0}
                  >
                    <CheckCircle size={18} />
                    Verify Document
                  </button>
                  <button className="btn-flag">
                    <Flag size={18} />
                    Request Re-upload
                  </button>
                  <button
                    className="btn-lock"
                    onClick={() => setShowLockModal(true)}
                    disabled={!canLock}
                    title={!canLock ? 'All documents must be verified to lock' : 'Lock application'}
                  >
                    <Lock size={18} />
                    Lock Application
                  </button>
                </>
              ) : (
                <div className="locked-notice">
                  <Lock size={18} />
                  <span>Application is locked</span>
                  <button 
                    className="btn-audit"
                    onClick={() => setShowAuditDrawer(true)}
                  >
                    <History size={16} />
                    View Audit Trail
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Cross Verification Summary */}
        {crossVerification && !crossVerification.name_consistent && (
          <div className="cross-verification-alert">
            <AlertCircle size={18} />
            <span>Name mismatch detected across documents: {crossVerification.mismatches?.join(', ')}</span>
          </div>
        )}
      </div>

      {/* Lock Confirmation Modal */}
      <Modal
        isOpen={showLockModal}
        onClose={() => setShowLockModal(false)}
        title="Lock Application"
      >
        <div className="lock-modal-content">
          <div className="lock-warning">
            <Shield size={48} className="warning-icon" />
            <h4>Once locked, data becomes immutable</h4>
            <p>This action cannot be undone without admin intervention. All verified data will be preserved and cannot be modified.</p>
          </div>
          <div className="modal-actions">
            <button 
              className="btn-cancel"
              onClick={() => setShowLockModal(false)}
            >
              Cancel
            </button>
            <button 
              className="btn-confirm-lock"
              onClick={() => lockMutation.mutate()}
              disabled={lockMutation.isPending}
            >
              {lockMutation.isPending ? 'Locking...' : 'Confirm Lock'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Unlock Request Modal (Admin only) */}
      <Modal
        isOpen={showUnlockModal}
        onClose={() => { setShowUnlockModal(false); setUnlockReason(''); }}
        title="Request Unlock"
      >
        <div className="unlock-modal-content">
          <p>Provide a reason for unlocking this application:</p>
          <textarea
            value={unlockReason}
            onChange={(e) => setUnlockReason(e.target.value)}
            placeholder="Enter reason for unlock..."
            rows={4}
            className="unlock-reason-input"
          />
          <div className="modal-actions">
            <button 
              className="btn-cancel"
              onClick={() => { setShowUnlockModal(false); setUnlockReason(''); }}
            >
              Cancel
            </button>
            <button 
              className="btn-confirm-unlock"
              onClick={() => unlockMutation.mutate(unlockReason)}
              disabled={!unlockReason.trim() || unlockMutation.isPending}
            >
              {unlockMutation.isPending ? 'Submitting...' : 'Submit Request'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Audit Trail Drawer */}
      <AuditTrailDrawer
        applicationId={appId}
        isOpen={showAuditDrawer}
        onClose={() => setShowAuditDrawer(false)}
      />
    </div>
  );
};