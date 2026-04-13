import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Send, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Upload,
  Loader,
  CreditCard
} from 'lucide-react';
import api from '../../services/api';
import './FeePaymentModal.css';

const QUOTA_LABELS = {
  general: 'General',
  obc: 'OBC',
  sc: 'SC',
  st: 'ST',
  management: 'Management',
  nri: 'NRI',
};

export const FeePaymentModal = ({ application, onClose }) => {
  const queryClient = useQueryClient();
  const [deadlineDays, setDeadlineDays] = useState(7);
  const [isSent, setIsSent] = useState(!!application.fee_instruction_sent_at);

  const sendMutation = useMutation({
    mutationFn: () => api.post(`/officer/${application.id}/send-fee-instructions/`, {
      fee_deadline_days: deadlineDays,
    }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['officer-application', application.id] });
      queryClient.invalidateQueries({ queryKey: ['officer-applications'] });
      setIsSent(true);
    },
  });

  const resendMutation = useMutation({
    mutationFn: () => api.post(`/officer/${application.id}/resend-fee-instructions/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['officer-application', application.id] });
    },
  });

  const isOverdue = application.fee_deadline && new Date(application.fee_deadline) < new Date();

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="fee-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Fee Payment Instructions</h3>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-content">
          <div className="student-summary">
            <span className="app-number">{application.application_number}</span>
            <span className="student-name">{application.student_profile?.full_name}</span>
          </div>

          <div className="allocation-info">
            <div className="info-row">
              <span>Branch:</span>
              <strong>{application.allocated_branch}</strong>
            </div>
            <div className="info-row">
              <span>Quota:</span>
              <strong>{QUOTA_LABELS[application.allocated_quota] || application.allocated_quota}</strong>
            </div>
          </div>

          <div className="fee-breakdown">
            <h4>Fee Breakdown</h4>
            <div className="fee-row">
              <span>Tuition Fee</span>
              <span>₹{application.fee_amount?.toLocaleString() || '0'}</span>
            </div>
            {application.fee_concession > 0 && (
              <div className="fee-row concession">
                <span>Concession</span>
                <span>-₹{application.fee_concession?.toLocaleString()}</span>
              </div>
            )}
            <div className="fee-row total">
              <span>Total</span>
              <span>₹{(application.fee_amount || 0).toLocaleString()}</span>
            </div>
          </div>

          <div className="payment-ref">
            <span>Reference ID:</span>
            <code>{application.payment_reference_id || 'Not generated'}</code>
          </div>

          {isSent ? (
            <div className="sent-status">
              <CheckCircle size={20} />
              <div>
                <span className="sent-label">Instructions Sent</span>
                {application.fee_deadline && (
                  <span className={`deadline-status ${isOverdue ? 'overdue' : ''}`}>
                    {isOverdue ? 'Deadline Passed' : `Due: ${new Date(application.fee_deadline).toLocaleDateString()}`}
                  </span>
                )}
              </div>
              <button 
                className="btn-secondary"
                onClick={() => resendMutation.mutate()}
                disabled={resendMutation.isPending}
              >
                {resendMutation.isPending ? <Loader size={16} /> : 'Resend'}
              </button>
            </div>
          ) : (
            <div className="deadline-input">
              <label>Fee Deadline (days from now):</label>
              <input
                type="number"
                value={deadlineDays}
                onChange={e => setDeadlineDays(parseInt(e.target.value))}
                min={1}
                max={30}
              />
            </div>
          )}

          <div className="email-preview">
            <h4>Email Preview</h4>
            <p>Student will receive an email with:</p>
            <ul>
              <li>Branch and quota details</li>
              <li>Complete fee breakdown</li>
              <li>Payment reference ID</li>
              <li>Bank details for payment</li>
              <li>Deadline date</li>
            </ul>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          {isSent ? (
            <button 
              className="btn-secondary"
              onClick={() => resendMutation.mutate()}
              disabled={resendMutation.isPending}
            >
              {resendMutation.isPending ? <Loader size={18} /> : 'Resend Email'}
            </button>
          ) : (
            <button 
              className="btn-primary"
              onClick={() => sendMutation.mutate()}
              disabled={sendMutation.isPending}
            >
              {sendMutation.isPending ? <Loader size={18} /> : <Send size={18} />}
              Send Instructions
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export const ConfirmPaymentModal = ({ application, onClose }) => {
  const queryClient = useQueryClient();
  const [paymentProof, setPaymentProof] = useState(null);
  const [showSuccess, setShowSuccess] = useState(false);

  const confirmMutation = useMutation({
    mutationFn: () => {
      const formData = new FormData();
      if (paymentProof) {
        formData.append('payment_proof_path', paymentProof);
      }
      return api.post(`/officer/${application.id}/confirm-payment/`, formData, {
        headers: paymentProof ? { 'Content-Type': 'multipart/form-data' } : {},
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['officer-application', application.id] });
      queryClient.invalidateQueries({ queryKey: ['officer-applications'] });
      setShowSuccess(true);
    },
  });

  const isOverdue = application.fee_deadline && new Date(application.fee_deadline) < new Date();

  if (showSuccess) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="success-modal" onClick={e => e.stopPropagation()}>
          <CheckCircle size={48} className="success-icon" />
          <h3>Admission Confirmed!</h3>
          <p>{application.student_profile?.full_name} has been admitted to {application.allocated_branch}.</p>
          <button className="btn-primary" onClick={onClose}>Done</button>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="confirm-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Confirm Payment</h3>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-content">
          <div className="warning-box">
            <AlertCircle size={20} />
            <span>This will mark the student as Admitted. This action cannot be undone.</span>
          </div>

          <div className="confirmation-details">
            <h4>{application.student_profile?.full_name}</h4>
            <p>{application.application_number}</p>
            <div className="detail-row">
              <span>Branch:</span>
              <strong>{application.allocated_branch}</strong>
            </div>
            <div className="detail-row">
              <span>Fee Paid:</span>
              <strong>₹{application.fee_amount?.toLocaleString()}</strong>
            </div>
            {isOverdue && (
              <div className="overdue-warning">
                Note: Payment deadline has passed
              </div>
            )}
          </div>

          <div className="proof-upload">
            <label>Payment Receipt (optional)</label>
            <div className="upload-area">
              <Upload size={24} />
              <span>Drop receipt image or click to browse</span>
              <input 
                type="file" 
                accept="image/*,.pdf"
                onChange={e => setPaymentProof(e.target.files[0])}
              />
            </div>
            {paymentProof && (
              <span className="file-name">{paymentProof.name}</span>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button 
            className="btn-success"
            onClick={() => confirmMutation.mutate()}
            disabled={confirmMutation.isPending}
          >
            {confirmMutation.isPending ? <Loader size={18} /> : <CheckCircle size={18} />}
            Confirm & Admit
          </button>
        </div>
      </div>
    </div>
  );
};

export const FeeStatusBadge = ({ application }) => {
  const isSent = !!application.fee_instruction_sent_at;
  const isPaid = application.fee_paid;
  const isOverdue = application.fee_deadline && new Date(application.fee_deadline) < new Date() && !isPaid;

  if (isPaid) {
    return <span className="fee-badge paid"><CheckCircle size={12} /> Paid</span>;
  }
  if (isOverdue) {
    return <span className="fee-badge overdue"><AlertCircle size={12} /> Overdue</span>;
  }
  if (isSent) {
    return <span className="fee-badge sent"><Clock size={12} /> Sent</span>;
  }
  return <span className="fee-badge not-sent">Not Sent</span>;
};

export default FeePaymentModal;