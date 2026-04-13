import React from 'react';
import './StatusBadge.css';

const STATUS_CONFIG = {
  verified: { label: 'Verified', className: 'status-verified' },
  locked: { label: 'Locked', className: 'status-locked' },
  allocated: { label: 'Seat Allocated', className: 'status-allocated' },
  fee_pending: { label: 'Fee Pending', className: 'status-fee-pending' },
  admitted: { label: 'Admitted', className: 'status-admitted' },
  rejected: { label: 'Rejected', className: 'status-rejected' },
  submitted: { label: 'Submitted', className: 'status-submitted' },
  under_verification: { label: 'Under Review', className: 'status-under-review' },
};

const FEE_STATUS_CONFIG = {
  not_sent: { label: 'Not Sent', className: 'fee-not-sent' },
  sent: { label: 'Sent', className: 'fee-sent' },
  overdue: { label: 'Overdue', className: 'fee-overdue' },
  paid: { label: 'Paid', className: 'fee-paid' },
};

export const StatusBadge = ({ status, showLabel = true }) => {
  const config = STATUS_CONFIG[status] || { label: status, className: 'status-default' };
  
  return (
    <span className={`status-badge ${config.className}`}>
      {showLabel && config.label}
    </span>
  );
};

export const FeeStatusBadge = ({ feeStatus, showLabel = true }) => {
  const config = FEE_STATUS_CONFIG[feeStatus] || { label: feeStatus, className: 'fee-default' };
  
  return (
    <span className={`status-badge ${config.className}`}>
      {showLabel && config.label}
    </span>
  );
};

export default StatusBadge;