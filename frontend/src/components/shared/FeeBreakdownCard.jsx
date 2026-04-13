import React from 'react';
import { IndianRupee, Building, FlaskRound, BookOpen, Home, CreditCard, FileText, Award } from 'lucide-react';
import './FeeBreakdownCard.css';

const FEE_TYPE_ICONS = {
  tuition: IndianRupee,
  hostel: Home,
  lab: FlaskRound,
  library: BookOpen,
  examination: FileText,
  sports: Award,
  other: CreditCard,
};

const FEE_TYPE_LABELS = {
  tuition: 'Tuition Fee',
  hostel: 'Hostel Fee',
  lab: 'Laboratory Fee',
  library: 'Library Fee',
  examination: 'Examination Fee',
  sports: 'Sports & Cultural Fee',
  other: 'Other Charges',
};

export const FeeBreakdownCard = ({ 
  feeData,
  paymentReference,
  showPaymentReference = true,
  compact = false 
}) => {
  if (!feeData) {
    return (
      <div className="fee-breakdown-card">
        <div className="fee-header">
          <h3>Fee Breakdown</h3>
        </div>
        <div className="fee-empty">
          <p>Fee information not available</p>
        </div>
      </div>
    );
  }

  const { line_items = [], total = 0, concession = 0, net_payable = 0 } = feeData;
  const hasConcession = concession > 0;

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const renderLineItem = (item, index) => {
    const Icon = FEE_TYPE_ICONS[item.fee_type] || CreditCard;
    const label = FEE_TYPE_LABELS[item.fee_type] || item.fee_type;
    const hasBreakdown = item.tuition_fee > 0 || item.hostel_fee > 0 || item.lab_fee > 0 || item.other_charges > 0;

    if (compact) {
      return (
        <div key={index} className="line-item compact">
          <div className="line-item-header">
            <Icon size={16} />
            <span className="fee-type">{label}</span>
          </div>
          <span className="fee-amount">{formatCurrency(item.total)}</span>
        </div>
      );
    }

    return (
      <div key={index} className="line-item">
        <div className="line-item-header">
          <Icon size={18} />
          <span className="fee-type">{label}</span>
        </div>
        
        {hasBreakdown && (
          <div className="breakdown-grid">
            {item.tuition_fee > 0 && (
              <div className="breakdown-item">
                <span>Tuition</span>
                <span>{formatCurrency(item.tuition_fee)}</span>
              </div>
            )}
            {item.hostel_fee > 0 && (
              <div className="breakdown-item">
                <span>Hostel</span>
                <span>{formatCurrency(item.hostel_fee)}</span>
              </div>
            )}
            {item.lab_fee > 0 && (
              <div className="breakdown-item">
                <span>Laboratory</span>
                <span>{formatCurrency(item.lab_fee)}</span>
              </div>
            )}
            {item.other_charges > 0 && (
              <div className="breakdown-item">
                <span>Other Charges</span>
                <span>{formatCurrency(item.other_charges)}</span>
              </div>
            )}
          </div>
        )}

        <div className="line-item-total">
          <span>Total</span>
          <strong>{formatCurrency(item.total)}</strong>
        </div>
      </div>
    );
  };

  return (
    <div className={`fee-breakdown-card ${compact ? 'compact' : ''}`}>
      <div className="fee-header">
        <h3>Fee Breakdown</h3>
        {showPaymentReference && paymentReference && (
          <div className="payment-ref">
            <FileText size={14} />
            <span>Payment Reference: {paymentReference}</span>
          </div>
        )}
      </div>

      <div className="fee-items">
        {line_items.map(renderLineItem)}
      </div>

      <div className="fee-summary">
        <div className="summary-row total-row">
          <span>Total Fee</span>
          <span className={hasConcession ? 'concession-strikethrough' : ''}>
            {formatCurrency(total)}
          </span>
        </div>

        {hasConcession && (
          <>
            <div className="summary-row concession-row">
              <span>Concession Applied</span>
              <span className="concession-amount">- {formatCurrency(concession)}</span>
            </div>
            <div className="summary-row adjusted-total">
              <span>Adjusted Total</span>
              <span>{formatCurrency(total - concession)}</span>
            </div>
          </>
        )}

        <div className="summary-row net-payable">
          <span>Net Payable</span>
          <strong>{formatCurrency(net_payable)}</strong>
        </div>

        {showPaymentReference && paymentReference && (
          <div className="summary-row payment-reference-row">
            <span>Payment Reference</span>
            <strong className="payment-ref-value">{paymentReference}</strong>
          </div>
        )}
      </div>

      {hasConcession && total > 0 && (
        <div className="concession-note">
          <Award size={14} />
          <span>Concession of {Math.round((concession / total) * 100)}% applied</span>
        </div>
      )}
    </div>
  );
};

export default FeeBreakdownCard;
