import React, { useState, useEffect } from 'react';
import { X, Send, Clock, AlertTriangle, CheckCircle, Upload } from 'lucide-react';
import { officerApi } from '../../services/officerApi';
import './FeeModal.css';

export const FeeModal = ({ application, onClose, onSuccess, showConfirmPayment: initialShowConfirmPayment = false }) => {
  const [deadlineDays, setDeadlineDays] = useState(7);
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [error, setError] = useState(null);
  const [showConfirmPayment, setShowConfirmPayment] = useState(initialShowConfirmPayment);
  const [paymentProof, setPaymentProof] = useState(null);
  const [overrideDeadline, setOverrideDeadline] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);

  const hasFeeInstructions = !!application?.fee_instruction_sent_at;
  const isOverdue = application?.fee_deadline && new Date(application.fee_deadline) < new Date() && !application?.fee_paid;

  const handleSendFeeInstructions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await officerApi.sendFeeInstructions(application.application_id, deadlineDays);
      onSuccess?.(response.data);
      onClose();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send fee instructions');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendFeeInstructions = async () => {
    setIsResending(true);
    setError(null);
    try {
      const response = await officerApi.resendFeeInstructions(application.application_id);
      onSuccess?.(response.data);
      onClose();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to resend fee instructions');
    } finally {
      setIsResending(false);
    }
  };

  const handleConfirmPayment = async () => {
    setPaymentLoading(true);
    setError(null);
    try {
      const response = await officerApi.confirmPayment(application.application_id, {
        override_deadline: overrideDeadline,
        payment_proof_path: paymentProof,
      });
      onSuccess?.(response.data);
      setShowConfirmPayment(false);
      onClose();
    } catch (err) {
      const warning = err.response?.data?.warning;
      if (warning && err.response?.data?.override_required) {
        setOverrideDeadline(true);
        setError('Payment deadline has passed. Enable override to confirm anyway.');
      } else {
        setError(err.response?.data?.error || 'Failed to confirm payment');
      }
    } finally {
      setPaymentLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPaymentProof(file.name);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return '-';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  if (showConfirmPayment) {
    return (
      <div className="fee-modal-overlay" onClick={onClose}>
        <div className="fee-modal confirm-payment-modal" onClick={e => e.stopPropagation()}>
          <div className="fee-modal-header">
            <h3>Confirm Payment</h3>
            <button className="modal-close" onClick={() => setShowConfirmPayment(false)}>
              <X size={20} />
            </button>
          </div>
          
          <div className="fee-modal-content">
            <div className="confirm-warning">
              <AlertTriangle size={24} />
              <p>This will mark the student as <strong>Admitted</strong>. This action cannot be undone.</p>
            </div>

            <div className="payment-details">
              <div className="detail-row">
                <span>Application Number:</span>
                <strong>{application?.application_number}</strong>
              </div>
              <div className="detail-row">
                <span>Student Name:</span>
                <strong>{application?.student_profile?.full_name}</strong>
              </div>
              <div className="detail-row">
                <span>Allocated Branch:</span>
                <strong>{application?.allocated_branch}</strong>
              </div>
              <div className="detail-row">
                <span>Fee Amount:</span>
                <strong>{formatCurrency(application?.fee_amount)}</strong>
              </div>
              {application?.fee_deadline && (
                <div className="detail-row">
                  <span>Deadline:</span>
                  <strong className={isOverdue ? 'text-danger' : ''}>
                    {formatDate(application.fee_deadline)}
                    {isOverdue && ' (OVERDUE)'}
                  </strong>
                </div>
              )}
            </div>

            <div className="payment-proof-upload">
              <label>
                <Upload size={18} />
                <span>Upload Payment Receipt (Optional)</span>
              </label>
              <input type="file" accept="image/*,.pdf" onChange={handleFileChange} />
              {paymentProof && <span className="file-name">{paymentProof}</span>}
            </div>

            {error && (
              <div className="error-message">
                <AlertTriangle size={16} />
                {error}
              </div>
            )}
          </div>

          <div className="fee-modal-footer">
            <button 
              className="btn-cancel" 
              onClick={() => setShowConfirmPayment(false)}
              disabled={paymentLoading}
            >
              Cancel
            </button>
            <button 
              className="btn-confirm-payment"
              onClick={handleConfirmPayment}
              disabled={paymentLoading}
            >
              {paymentLoading ? 'Confirming...' : 'Confirm Payment'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fee-modal-overlay" onClick={onClose}>
      <div className="fee-modal" onClick={e => e.stopPropagation()}>
        <div className="fee-modal-header">
          <h3>{hasFeeInstructions ? 'Fee Instructions Sent' : 'Send Fee Instructions'}</h3>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="fee-modal-content">
          {hasFeeInstructions && (
            <div className="fee-sent-info">
              <div className="sent-badge">
                <CheckCircle size={16} />
                Sent on {formatDate(application.fee_instruction_sent_at)}
              </div>
              {application?.fee_deadline && (
                <div className={`deadline-info ${isOverdue ? 'overdue' : ''}`}>
                  <Clock size={16} />
                  Deadline: {formatDate(application.fee_deadline)}
                  {isOverdue && <span className="overdue-badge">OVERDUE</span>}
                </div>
              )}
            </div>
          )}

          <div className="fee-breakdown">
            <h4>Fee Breakdown</h4>
            <div className="fee-items">
              <div className="fee-item">
                <span>Tuition Fee</span>
                <span>{formatCurrency(application?.fee_amount || 50000)}</span>
              </div>
              <div className="fee-item">
                <span>Hostel Fee (Optional)</span>
                <span>{formatCurrency(0)}</span>
              </div>
              <div className="fee-item">
                <span>Lab & Other Charges</span>
                <span>{formatCurrency(0)}</span>
              </div>
              <div className="fee-item total">
                <span>Total</span>
                <span>{formatCurrency(application?.fee_amount || 50000)}</span>
              </div>
              {application?.fee_concession > 0 && (
                <div className="fee-item concession">
                  <span>Concession</span>
                  <span>-{formatCurrency(application.fee_concession)}</span>
                </div>
              )}
              <div className="fee-item net-payable">
                <span>Net Payable</span>
                <span>{formatCurrency(application?.fee_amount || 50000)}</span>
              </div>
            </div>
          </div>

          {!hasFeeInstructions && (
            <div className="deadline-picker">
              <label>Payment Deadline</label>
              <select 
                value={deadlineDays} 
                onChange={(e) => setDeadlineDays(Number(e.target.value))}
              >
                <option value={3}>3 Days</option>
                <option value={5}>5 Days</option>
                <option value={7}>7 Days</option>
                <option value={10}>10 Days</option>
                <option value={14}>14 Days</option>
              </select>
            </div>
          )}

          <div className="email-preview">
            <h4>Email Preview</h4>
            <div className="preview-content">
              <p><strong>Subject:</strong> Fee Payment Details - {application?.application_number}</p>
              <p><strong>To:</strong> {application?.student_profile?.email}</p>
              <div className="preview-body">
                Dear {application?.student_profile?.full_name},<br/><br/>
                Your admission to {application?.allocated_branch} ({application?.allocated_quota}) has been approved.<br/><br/>
                <strong>Fee Details:</strong><br/>
                Net Payable: {formatCurrency(application?.fee_amount || 50000)}<br/>
                Payment Reference: PAY-{application?.application_number}-XXXXXX<br/>
                Deadline: {hasFeeInstructions ? formatDate(application?.fee_deadline) : `${deadlineDays} days from now`}<br/><br/>
                Please make the payment via NEFT/RTGS to the college account.
              </div>
            </div>
          </div>

          {error && (
            <div className="error-message">
              <AlertTriangle size={16} />
              {error}
            </div>
          )}
        </div>

        <div className="fee-modal-footer">
          <button className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          
          {hasFeeInstructions ? (
            <button 
              className="btn-resend" 
              onClick={handleResendFeeInstructions}
              disabled={isResending}
            >
              <Send size={16} />
              {isResending ? 'Resending...' : 'Resend Instructions'}
            </button>
          ) : (
            <button 
              className="btn-send" 
              onClick={handleSendFeeInstructions}
              disabled={isLoading}
            >
              <Send size={16} />
              {isLoading ? 'Sending...' : 'Send Instructions'}
            </button>
          )}

          {hasFeeInstructions && !application?.fee_paid && (
            <button 
              className="btn-confirm" 
              onClick={() => setShowConfirmPayment(true)}
            >
              <CheckCircle size={16} />
              Confirm Payment
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default FeeModal;
