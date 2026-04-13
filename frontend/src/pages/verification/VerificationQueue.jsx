import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  ClipboardList, 
  CheckCircle2, 
  AlertCircle, 
  XCircle, 
  UserCheck, 
  BarChart3, 
  Clock, 
  Search, 
  Filter,
  History,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Upload
} from 'lucide-react';
import { verificationApi } from '../../services/verificationApi';
import { authApi } from '../../services/authApi';
import { PageHeader } from '../../components/layout/PageHeader';
import { useDebounce } from '../../hooks/useDebounce';
import toast from 'react-hot-toast';
import './VerificationQueue.css';

import { ConfidenceDots } from '../../components/verification/ConfidenceDots';

const StatCard = ({ title, value, icon: Icon, color, onClick, active, subtitle }) => (
  <div 
    className={`stat-card ${color} ${active ? 'active' : ''} ${onClick ? 'clickable' : ''}`}
    onClick={onClick}
  >
    <div className="stat-card-glass"></div>
    <div className="stat-card-content">
      <div className="stat-icon-wrapper"><Icon size={24} /></div>
      <div className="stat-text">
        <span className="stat-title">{title}</span>
        <span className="stat-value">{value}</span>
        {subtitle && <span className="stat-subtitle">{subtitle}</span>}
      </div>
    </div>
  </div>
);

import { MyClaimsPanel } from '../../components/verification/MyClaimsPanel';
import { Modal } from '../../components/ui/Modal';

export const VerificationQueue = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showMaxClaimsModal, setShowMaxClaimsModal] = useState(false);
  const [newlyAddedIds, setNewlyAddedIds] = useState(new Set());
  const [prevIds, setPrevIds] = useState(new Set());
  
  const selectedConfidence = searchParams.get('confidence') || '';
  const selectedStatus = searchParams.get('status') || '';
  const selectedSort = searchParams.get('sort') || 'confidence';
  const initialSearch = searchParams.get('search') || '';
  const page = parseInt(searchParams.get('page')) || 1;

  // Get current user
  const { data: currentUser } = useQuery({
    queryKey: ['current-user'],
    queryFn: () => authApi.getCurrentUser().then(res => res.data),
  });

  const [searchInput, setSearchInput] = useState(initialSearch);
  const debouncedSearch = useDebounce(searchInput, 300);

  useEffect(() => {
    updateUrlParams({ search: debouncedSearch, page: 1 });
  }, [debouncedSearch]);

  const updateUrlParams = (newParams) => {
    const params = new URLSearchParams(searchParams);
    Object.entries(newParams).forEach(([key, value]) => {
      if (value) params.set(key, value);
      else params.delete(key);
    });
    setSearchParams(params, { replace: true });
  };

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['verification-stats'],
    queryFn: () => verificationApi.getQueueStats().then(res => res.data),
    refetchInterval: 30000,
  });

  const { data: queueData, isLoading: queueLoading } = useQuery({
    queryKey: ['verification-queue', selectedConfidence, selectedStatus, selectedSort, debouncedSearch, page],
    queryFn: () => verificationApi.getQueue({
      confidence: selectedConfidence,
      status: selectedStatus,
      sort: selectedSort,
      search: debouncedSearch,
      page: page
    }).then(res => res.data),
    refetchInterval: 30000,
  });

  // Animation tracker for new items
  useEffect(() => {
    if (queueData?.results) {
      const currentIds = new Set(queueData.results.map(a => a.application_id));
      if (prevIds.size > 0) {
        const newIds = new Set([...currentIds].filter(id => !prevIds.has(id)));
        if (newIds.size > 0) {
          setNewlyAddedIds(newIds);
          setTimeout(() => setNewlyAddedIds(new Set()), 5000);
        }
      }
      setPrevIds(currentIds);
    }
  }, [queueData?.results]);

  const claimMutation = useMutation({
    mutationFn: (id) => verificationApi.claimApplication(id),
    onSuccess: (res) => {
      toast.success('Application claimed successfully');
      navigate(`/verification/review/${res.data.application_id}`);
    },
    onError: (err) => {
      if (err.response?.status === 409) {
        toast.error('This application is already being reviewed by another staff member');
      } else {
        toast.error(err.response?.data?.error || 'Failed to claim application');
      }
      // Refresh to update claim status
      queryClient.invalidateQueries({ queryKey: ['verification-queue'] });
      queryClient.invalidateQueries({ queryKey: ['verification-stats'] });
    }
  });

  const handleReviewClick = (id) => {
    if (stats?.my_claimed >= 3) {
      setShowMaxClaimsModal(true);
      return;
    }
    claimMutation.mutate(id);
  };

  const handleConfidenceClick = (level) => {
    updateUrlParams({ confidence: selectedConfidence === level ? '' : level, page: 1 });
  };

  if (statsLoading) return <div className="loading-overlay">Initializing Dashboard...</div>;

  return (
    <div className="verification-queue-page">
      <PageHeader 
        title="Verification Queue" 
        subtitle="Manage and validate student applications with OCR-assisted scoring"
      />

      <section className="stats-header-grid">
        <StatCard title="Pending Total" value={stats?.total_pending || 0} icon={ClipboardList} color="primary" subtitle={`${stats?.by_status?.submitted || 0} New, ${stats?.by_status?.under_verification || 0} In Progress`} />
        <StatCard title="High Confidence" value={stats?.by_confidence?.high || 0} icon={CheckCircle2} color="success" onClick={() => handleConfidenceClick('high')} active={selectedConfidence === 'high'} subtitle="Ready for quick verification" />
        <StatCard title="Medium Confidence" value={stats?.by_confidence?.medium || 0} icon={AlertCircle} color="warning" onClick={() => handleConfidenceClick('medium')} active={selectedConfidence === 'medium'} subtitle="Minor corrections likely" />
        <StatCard title="Low Confidence" value={stats?.by_confidence?.low || 0} icon={XCircle} color="danger" onClick={() => handleConfidenceClick('low')} active={selectedConfidence === 'low'} subtitle="Manual entry required" />
      </section>

      <section className="stats-footer-row">
        <div className="footer-stat"><UserCheck size={18} /><span>My Claims: <strong>{stats?.my_claimed}</strong></span></div>
        <div className="footer-stat"><BarChart3 size={18} /><span>Avg Confidence: <strong>{Math.round(stats?.average_confidence * 100)}%</strong></span></div>
        <div className="footer-stat"><Clock size={18} /><span>Oldest Pending: <strong>{stats?.oldest_pending}</strong></span></div>
      </section>

      <MyClaimsPanel />

      <section className="filter-bar">
        <div className="search-wrapper">
          <Search className="search-icon" size={20} />
          <input type="text" placeholder="Search by name, app #, or email..." value={searchInput} onChange={(e) => setSearchInput(e.target.value)} />
        </div>
        <div className="filter-group">
          <div className="select-wrapper">
            <Filter size={16} className="select-icon" /><select value={selectedConfidence} onChange={(e) => updateUrlParams({ confidence: e.target.value, page: 1 })}><option value="">All Confidence</option><option value="high">High (Green)</option><option value="medium">Medium (Yellow)</option><option value="low">Low (Red)</option></select>
          </div>
          <div className="select-wrapper">
            <ClipboardList size={16} className="select-icon" /><select value={selectedStatus} onChange={(e) => updateUrlParams({ status: e.target.value, page: 1 })}><option value="">All Statuses</option><option value="submitted">Submitted</option><option value="under_verification">Under Verification</option></select>
          </div>
          <div className="select-wrapper">
            <History size={16} className="select-icon" /><select value={selectedSort} onChange={(e) => updateUrlParams({ sort: e.target.value, page: 1 })}><option value="confidence">Confidence (Low → High)</option><option value="confidence_desc">Confidence (High → Low)</option><option value="submitted_at">Oldest First</option><option value="-submitted_at">Newest First</option></select>
          </div>
        </div>
      </section>

      <div className="queue-table-container">
        {queueLoading ? (
          <div className="table-loading">Updating queue results...</div>
        ) : (
          <>
            <table className="queue-table">
              <thead>
                <tr>
                  <th>App #</th>
                  <th>Student</th>
                  <th>Docs</th>
                  <th>Document Confidence</th>
                  <th>Overall</th>
                  <th>Submitted</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {queueData?.results?.map((app) => (
                  <tr 
                    key={app.application_id} 
                    className={`
                      conf-row-${app.confidence_badge.level} 
                      ${newlyAddedIds.has(app.application_id) ? 'row-flash' : ''}
                      ${app.is_claimed && app.claimed_by !== currentUser?.id ? 'row-claimed' : ''}
                      ${app.rejected_documents_count > 0 ? 'row-rejected' : ''}
                    `}
                  >
                    <td className="font-mono">
                      <div className="app-id-cell">
                        {app.application_number}
                        {app.rejected_documents_count > 0 && (
                          <span className="rejected-indicator" title={`${app.rejected_documents_count} document(s) awaiting re-upload`}>
                            <Upload size={12} />
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="student-info">
                        <span className="student-name">{app.student_name}</span>
                        <span className="student-email">{app.student_email}</span>
                      </div>
                    </td>
                    <td>{app.documents_summary.filter(d => d.status === 'extracted').length}/{app.documents_count}</td>
                    <td>
                      <ConfidenceDots documents={app.documents_summary} />
                    </td>
                    <td>
                      <div className={`overall-badge ${app.confidence_badge.level}`}>
                        {app.confidence_badge.level === 'high' && <CheckCircle2 size={12} />}
                        {app.confidence_badge.level === 'medium' && <AlertCircle size={12} />}
                        {app.confidence_badge.level === 'low' && <XCircle size={12} />}
                        {Math.round(app.overall_confidence * 100)}%
                      </div>
                    </td>
                    <td>
                      <span className="submitted-time" title={new Date(app.submitted_at).toLocaleString()}>
                        {app.time_since_submission}
                      </span>
                    </td>
                    <td>
                      {app.is_claimed && app.claimed_by !== currentUser?.id ? (
                        <div className="claimed-badge">
                          <UserCheck size={12} />
                          Being Reviewed
                        </div>
                      ) : (
                        <button 
                          className="review-btn"
                          onClick={() => handleReviewClick(app.application_id)}
                          disabled={claimMutation.isPending}
                        >
                          {claimMutation.isPending ? 'Claiming...' : 'Review'}
                          <ExternalLink size={14} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {!queueData?.results?.length && (
                  <tr>
                    <td colSpan="7" className="empty-row">No applications found matching your filters.</td>
                  </tr>
                )}
              </tbody>
            </table>

            {/* Pagination */}
            {queueData?.count > 0 && (
              <div className="pagination">
                <div className="pagination-info">
                  Showing {(page - 1) * 20 + 1}-{Math.min(page * 20, queueData.count)} of {queueData.count}
                </div>
                <div className="pagination-controls">
                  <button 
                    disabled={page === 1} 
                    onClick={() => updateUrlParams({ page: page - 1 })}
                  ><ChevronLeft size={18} /></button>
                  <span className="page-current">{page}</span>
                  <button 
                    disabled={!queueData.next} 
                    onClick={() => updateUrlParams({ page: page + 1 })}
                  ><ChevronRight size={18} /></button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Max Claims Modal */}
      <Modal 
        isOpen={showMaxClaimsModal} 
        onClose={() => setShowMaxClaimsModal(false)}
        title="Active Review Limit Reached"
      >
        <div className="max-claims-modal">
          <p className="mb-6 text-gray-600">
            You currently have 3 active application reviews. To maintain system efficiency and ensure timely processing, you must complete or release one of your current reviews before claiming a new application.
          </p>
          <div className="flex justify-end gap-3">
            <button 
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium"
              onClick={() => setShowMaxClaimsModal(false)}
            >
              Close
            </button>
            <button 
              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium"
              onClick={() => {
                setShowMaxClaimsModal(false);
                // Scroll up to claims panel
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            >
              View My Claims
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
