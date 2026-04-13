import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Check, X, DollarSign, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { principalApi } from '../../services/principalApi';
import { PageHeader } from '../../components/layout/PageHeader';
import { StatCard } from '../../components/ui/StatCard';
import './AdminCommissions.css';

const getStatusBadgeColor = (status) => {
  switch (status) {
    case 'pending':
      return '#F59E0B'; // amber
    case 'approved':
      return '#3B82F6'; // blue
    case 'paid':
      return '#10B981'; // green
    case 'rejected':
      return '#EF4444'; // red
    default:
      return '#6B7280'; // gray
  }
};

const getStatusLabel = (status) => {
  return status.charAt(0).toUpperCase() + status.slice(1);
};

export function AdminCommissions() {
  const [filterStatus, setFilterStatus] = useState('');
  const [filterAgent, setFilterAgent] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [expandedId, setExpandedId] = useState(null);
  const [selectedCommissions, setSelectedCommissions] = useState(new Set());
  const [showBulkPayModal, setShowBulkPayModal] = useState(false);
  const [paymentRef, setPaymentRef] = useState('');

  const queryClient = useQueryClient();

  // Fetch commissions list
  const { data: commissionsData, isLoading } = useQuery({
    queryKey: ['admin-commissions', filterStatus, filterAgent, dateFrom, dateTo],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filterStatus) params.append('status', filterStatus);
      if (filterAgent) params.append('agent', filterAgent);
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);
      return principalApi.getAdminCommissions(params).then((r) => r.data);
    },
    refetchInterval: 60000,
  });

  // Fetch agents for filter dropdown
  const { data: agentsData } = useQuery({
    queryKey: ['admin-agents'],
    queryFn: () => principalApi.getAdminAgents().then((r) => r.data),
  });

  const sortedCommissions = useMemo(() => {
    if (!commissionsData?.results) return [];

    const commissions = [...commissionsData.results];
    commissions.sort((a, b) => {
      let aVal, bVal;

      switch (sortBy) {
        case 'agent_name':
          aVal = a.agent_name?.toLowerCase() || '';
          bVal = b.agent_name?.toLowerCase() || '';
          return sortOrder === 'desc' ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
        case 'student_name':
          aVal = a.student_name?.toLowerCase() || '';
          bVal = b.student_name?.toLowerCase() || '';
          return sortOrder === 'desc' ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
        case 'amount':
          aVal = parseFloat(a.commission_amount || 0);
          bVal = parseFloat(b.commission_amount || 0);
          break;
        case 'status':
          aVal = a.status;
          bVal = b.status;
          return sortOrder === 'desc' ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
        default:
          aVal = new Date(a.created_at);
          bVal = new Date(b.created_at);
          break;
      }

      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
    });

    return commissions;
  }, [commissionsData, sortBy, sortOrder]);

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  const SortIcon = ({ column }) => {
    if (sortBy !== column) return <span className="sort-icon inactive">⇅</span>;
    return sortOrder === 'desc' ? (
      <span className="sort-icon active">↓</span>
    ) : (
      <span className="sort-icon active">↑</span>
    );
  };

  // Mutations
  const approveMutation = useMutation({
    mutationFn: (commissionId) => principalApi.approveCommission(commissionId),
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-commissions']);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ commissionId, notes }) =>
      principalApi.rejectCommission(commissionId, { notes }),
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-commissions']);
    },
  });

  const markPaidMutation = useMutation({
    mutationFn: ({ commissionId, paymentReference }) =>
      principalApi.markCommissionPaid(commissionId, { payment_reference: paymentReference }),
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-commissions']);
    },
  });

  const bulkPayMutation = useMutation({
    mutationFn: ({ commissionIds, paymentReference }) =>
      principalApi.bulkPayCommissions({
        commission_ids: Array.from(commissionIds),
        payment_reference: paymentReference,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-commissions']);
      setSelectedCommissions(new Set());
      setShowBulkPayModal(false);
      setPaymentRef('');
    },
  });

  const toggleSelection = (commissionId) => {
    const newSelection = new Set(selectedCommissions);
    if (newSelection.has(commissionId)) {
      newSelection.delete(commissionId);
    } else {
      newSelection.add(commissionId);
    }
    setSelectedCommissions(newSelection);
  };

  const toggleSelectAll = () => {
    if (selectedCommissions.size === sortedCommissions.length) {
      setSelectedCommissions(new Set());
    } else {
      setSelectedCommissions(new Set(sortedCommissions.map((c) => c.id)));
    }
  };

  if (isLoading) {
    return <div className="loading-overlay">Loading commissions...</div>;
  }

  const selectedCount = selectedCommissions.size;
  const selectedAmount = Array.from(selectedCommissions).reduce((sum, id) => {
    const commission = sortedCommissions.find((c) => c.id === id);
    return sum + parseFloat(commission?.commission_amount || 0);
  }, 0);

  return (
    <div className="admin-commissions-page">
      <PageHeader
        title="Commission Management"
        subtitle="Approve, reject, and manage agent commissions"
      />

      {/* Summary Cards */}
      <section className="stats-grid">
        <StatCard
          title="Pending Commissions"
          value={commissionsData?.summary?.pending_count || 0}
          icon={FileText}
          color="warning"
        />
        <StatCard
          title="Pending Amount"
          value={`₹${parseFloat(commissionsData?.summary?.pending_amount || 0).toLocaleString('en-IN', {
            maximumFractionDigits: 0,
          })}`}
          icon={DollarSign}
          color="warning"
        />
        <StatCard
          title="Ready to Pay"
          value={commissionsData?.summary?.approved_count || 0}
          icon={Check}
          color="info"
        />
        <StatCard
          title="Approved Amount"
          value={`₹${parseFloat(commissionsData?.summary?.approved_amount || 0).toLocaleString('en-IN', {
            maximumFractionDigits: 0,
          })}`}
          icon={DollarSign}
          color="info"
        />
      </section>

      {/* Filters */}
      <section className="filters-section">
        <div className="filter-group">
          <label>Status</label>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="paid">Paid</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Agent</label>
          <select value={filterAgent} onChange={(e) => setFilterAgent(e.target.value)}>
            <option value="">All Agents</option>
            {agentsData?.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.agency_name || agent.full_name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>From</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>To</label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>
      </section>

      {/* Bulk Actions */}
      {selectedCount > 0 && (
        <section className="bulk-actions">
          <div className="bulk-summary">
            <span>{selectedCount} commission(s) selected</span>
            <span className="amount">₹{selectedAmount.toLocaleString('en-IN')}</span>
          </div>
          <button
            className="bulk-pay-btn"
            onClick={() => setShowBulkPayModal(true)}
          >
            Mark as Paid
          </button>
        </section>
      )}

      {/* Bulk Pay Modal */}
      {showBulkPayModal && (
        <div className="modal-overlay" onClick={() => setShowBulkPayModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Mark {selectedCount} Commission(s) as Paid</h3>
            <div className="modal-body">
              <p className="amount-summary">
                Total Amount: ₹{selectedAmount.toLocaleString('en-IN')}
              </p>
              <div className="form-group">
                <label>Payment Reference Number</label>
                <input
                  type="text"
                  placeholder="e.g., BANK-TRF-20240315-001"
                  value={paymentRef}
                  onChange={(e) => setPaymentRef(e.target.value)}
                />
              </div>
            </div>
            <div className="modal-actions">
              <button
                className="btn-secondary"
                onClick={() => setShowBulkPayModal(false)}
              >
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={() =>
                  bulkPayMutation.mutate({
                    commissionIds: selectedCommissions,
                    paymentReference: paymentRef,
                  })
                }
                disabled={!paymentRef || bulkPayMutation.isPending}
              >
                {bulkPayMutation.isPending ? 'Processing...' : 'Confirm Payment'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Commissions Table */}
      <section className="commissions-table-container">
        <table className="commissions-table">
          <thead>
            <tr>
              <th>
                <input
                  type="checkbox"
                  checked={selectedCount === sortedCommissions.length && sortedCommissions.length > 0}
                  onChange={toggleSelectAll}
                />
              </th>
              <th>
                <button className="sort-header" onClick={() => handleSort('agent_name')}>
                  Agent <SortIcon column="agent_name" />
                </button>
              </th>
              <th>
                <button className="sort-header" onClick={() => handleSort('student_name')}>
                  Student <SortIcon column="student_name" />
                </button>
              </th>
              <th>Application</th>
              <th>
                <button className="sort-header" onClick={() => handleSort('amount')}>
                  Amount <SortIcon column="amount" />
                </button>
              </th>
              <th>
                <button className="sort-header" onClick={() => handleSort('status')}>
                  Status <SortIcon column="status" />
                </button>
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedCommissions.map((commission) => (
              <React.Fragment key={commission.id}>
                <tr className="commission-row">
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedCommissions.has(commission.id)}
                      onChange={() => toggleSelection(commission.id)}
                    />
                  </td>
                  <td className="agent-name">{commission.agent_name}</td>
                  <td className="student-name">{commission.student_name}</td>
                  <td className="app-number">{commission.application_number}</td>
                  <td className="amount">₹{parseFloat(commission.commission_amount).toLocaleString('en-IN')}</td>
                  <td>
                    <span
                      className="status-badge"
                      style={{ backgroundColor: getStatusBadgeColor(commission.status) }}
                    >
                      {getStatusLabel(commission.status)}
                    </span>
                  </td>
                  <td>
                    <button
                      className="expand-btn"
                      onClick={() =>
                        setExpandedId(expandedId === commission.id ? null : commission.id)
                      }
                      title="View details"
                    >
                      {expandedId === commission.id ? (
                        <ChevronUp size={18} />
                      ) : (
                        <ChevronDown size={18} />
                      )}
                    </button>
                  </td>
                </tr>

                {/* Expanded Details */}
                {expandedId === commission.id && (
                  <tr className="expanded-row">
                    <td colSpan="7">
                      <CommissionDetails
                        commission={commission}
                        onApprove={() => approveMutation.mutate(commission.id)}
                        onReject={(notes) =>
                          rejectMutation.mutate({ commissionId: commission.id, notes })
                        }
                        onMarkPaid={(paymentRef) =>
                          markPaidMutation.mutate({
                            commissionId: commission.id,
                            paymentReference: paymentRef,
                          })
                        }
                        approvePending={approveMutation.isPending}
                        rejectPending={rejectMutation.isPending}
                        markPaidPending={markPaidMutation.isPending}
                      />
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>

        {sortedCommissions.length === 0 && (
          <div className="empty-state">
            <p>No commissions found</p>
          </div>
        )}
      </section>
    </div>
  );
}

function CommissionDetails({
  commission,
  onApprove,
  onReject,
  onMarkPaid,
  approvePending,
  rejectPending,
  markPaidPending,
}) {
  const [rejectNotes, setRejectNotes] = useState('');
  const [paymentRef, setPaymentRef] = useState('');
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [showPaymentForm, setShowPaymentForm] = useState(false);

  return (
    <div className="commission-details">
      <div className="details-grid">
        <div className="detail-item">
          <label>Fee Amount</label>
          <span>₹{parseFloat(commission.fee_amount).toLocaleString('en-IN')}</span>
        </div>
        <div className="detail-item">
          <label>Commission Rate</label>
          <span>{commission.commission_rate}%</span>
        </div>
        <div className="detail-item">
          <label>Branch</label>
          <span>{commission.branch_name || '—'}</span>
        </div>
        {commission.notes && (
          <div className="detail-item">
            <label>Notes</label>
            <span>{commission.notes}</span>
          </div>
        )}
        {commission.payment_reference && (
          <div className="detail-item">
            <label>Payment Reference</label>
            <span>{commission.payment_reference}</span>
          </div>
        )}
      </div>

      {/* Actions */}
      {commission.status === 'pending' && (
        <div className="actions-section">
          <button
            className="btn-approve"
            onClick={onApprove}
            disabled={approvePending}
          >
            <Check size={16} /> Approve
          </button>

          {!showRejectForm ? (
            <button
              className="btn-reject"
              onClick={() => setShowRejectForm(true)}
            >
              <X size={16} /> Reject
            </button>
          ) : (
            <div className="reject-form">
              <textarea
                placeholder="Reason for rejection..."
                value={rejectNotes}
                onChange={(e) => setRejectNotes(e.target.value)}
              />
              <div className="form-actions">
                <button
                  className="btn-cancel"
                  onClick={() => setShowRejectForm(false)}
                >
                  Cancel
                </button>
                <button
                  className="btn-confirm"
                  onClick={() => {
                    onReject(rejectNotes);
                    setShowRejectForm(false);
                    setRejectNotes('');
                  }}
                  disabled={!rejectNotes || rejectPending}
                >
                  Confirm Rejection
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {commission.status === 'approved' && (
        <div className="actions-section">
          {!showPaymentForm ? (
            <button
              className="btn-pay"
              onClick={() => setShowPaymentForm(true)}
            >
              <DollarSign size={16} /> Mark as Paid
            </button>
          ) : (
            <div className="payment-form">
              <input
                type="text"
                placeholder="Payment reference number"
                value={paymentRef}
                onChange={(e) => setPaymentRef(e.target.value)}
              />
              <div className="form-actions">
                <button
                  className="btn-cancel"
                  onClick={() => setShowPaymentForm(false)}
                >
                  Cancel
                </button>
                <button
                  className="btn-confirm"
                  onClick={() => {
                    onMarkPaid(paymentRef);
                    setShowPaymentForm(false);
                    setPaymentRef('');
                  }}
                  disabled={!paymentRef || markPaidPending}
                >
                  Confirm Payment
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
