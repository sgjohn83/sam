import React from 'react';
import { 
  ChevronLeft, 
  ChevronRight,
  Search,
  X,
  ArrowUpDown,
  ChevronUp,
  ChevronDown
} from 'lucide-react';
import { StatusBadge, FeeStatusBadge } from './StatusBadge';
import './ApplicationTable.css';

const STATUS_OPTIONS = [
  { value: '', label: 'All Status' },
  { value: 'verified', label: 'Verified' },
  { value: 'allocated', label: 'Allocated' },
  { value: 'fee_pending', label: 'Fee Pending' },
  { value: 'admitted', label: 'Admitted' },
  { value: 'rejected', label: 'Rejected' },
];

const FEE_STATUS_OPTIONS = [
  { value: '', label: 'All Fee Status' },
  { value: 'not_sent', label: 'Not Sent' },
  { value: 'sent', label: 'Sent' },
  { value: 'overdue', label: 'Overdue' },
  { value: 'paid', label: 'Paid' },
];

const QUOTA_OPTIONS = [
  { value: '', label: 'All Quotas' },
  { value: 'general', label: 'General' },
  { value: 'management', label: 'Management' },
  { value: 'nri', label: 'NRI' },
  { value: 'sports', label: 'Sports' },
  { value: 'staff', label: 'Staff' },
];

const CATEGORY_OPTIONS = [
  { value: '', label: 'All Categories' },
  { value: 'general', label: 'General' },
  { value: 'obc', label: 'OBC' },
  { value: 'sc', label: 'SC' },
  { value: 'st', label: 'ST' },
];

const PAGE_SIZE_OPTIONS = [10, 25, 50];

export const ApplicationTable = ({ 
  applications, 
  isLoading, 
  pagination,
  onPageChange,
  onPageSizeChange,
  onSort,
  sortBy,
  sortOrder,
  onSearch,
  searchValue,
  filters = {},
  onFilterChange,
  branches = [],
}) => {
  const getStatusFromApp = (app) => {
    if (app.is_locked) return 'locked';
    return app.status;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      day: '2-digit', 
      month: 'short', 
      year: 'numeric' 
    });
  };

  const formatMeritScore = (score) => {
    if (score === null || score === undefined) return '-';
    return score.toLocaleString();
  };

  const getFirstBranchPreference = (prefs) => {
    if (!prefs || prefs.length === 0) return '-';
    return 'Branch';
  };

  const activeFilters = Object.entries(filters).filter(([, value]) => value && value !== '');

  const getFilterLabel = (key, value) => {
    const labels = {
      status: STATUS_OPTIONS.find(o => o.value === value)?.label,
      quota: QUOTA_OPTIONS.find(o => o.value === value)?.label,
      category: CATEGORY_OPTIONS.find(o => o.value === value)?.label,
      branch_id: branches.find(b => b.id === value)?.name,
      search: `Search: "${value}"`,
    };
    return labels[key] || value;
  };

  const handleRemoveFilter = (key) => {
    onFilterChange?.(key, '');
  };

  const handleClearAllFilters = () => {
    onFilterChange?.(null, null);
  };

  const getSortIcon = (field) => {
    if (sortBy !== field) return <ArrowUpDown size={14} />;
    return sortOrder === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />;
  };

  const renderSkeletonRow = (index) => (
    <tr key={`skeleton-${index}`} className="skeleton-row">
      <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
      <td><div className="skeleton skeleton-text" style={{ width: '140px' }} /></td>
      <td><div className="skeleton skeleton-text" style={{ width: '60px' }} /></td>
      <td><div className="skeleton skeleton-text" style={{ width: '40px' }} /></td>
      <td><div className="skeleton skeleton-text" style={{ width: '60px' }} /></td>
      <td><div className="skeleton skeleton-text" style={{ width: '50px' }} /></td>
      <td><div className="skeleton skeleton-badge" /></td>
      <td><div className="skeleton skeleton-badge" /></td>
      <td><div className="skeleton skeleton-text" style={{ width: '70px' }} /></td>
    </tr>
  );

  const renderEmptyState = () => (
    <tr>
      <td colSpan="9" className="empty-state">
        <div className="empty-illustration">
          <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="60" cy="60" r="50" fill="#F3F4F6" />
            <path d="M40 55C40 48.3726 45.3726 43 52 43H68C74.6274 43 80 48.3726 80 55V65C80 71.6274 74.6274 77 68 77H52C45.3726 77 40 71.6274 40 65V55Z" fill="white" stroke="#D1D5DB" strokeWidth="2" />
            <path d="M45 60H75" stroke="#D1D5DB" strokeWidth="2" strokeLinecap="round" />
            <path d="M45 67H65" stroke="#D1D5DB" strokeWidth="2" strokeLinecap="round" />
            <circle cx="60" cy="35" r="8" fill="#E5E7EB" />
            <path d="M55 47L58 50L65 43" stroke="#D1D5DB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <h3 className="empty-title">No Applications Found</h3>
        <p className="empty-message">
          {activeFilters.length > 0 
            ? "No applications match your current filters. Try adjusting your search criteria."
            : "There are no applications to display at this time."}
        </p>
        {activeFilters.length > 0 && (
          <button className="empty-clear-btn" onClick={handleClearAllFilters}>
            Clear All Filters
          </button>
        )}
      </td>
    </tr>
  );

  if (isLoading) {
    return (
      <div className="application-table-container">
        <div className="filter-bar">
          <div className="search-box">
            <div className="skeleton" style={{ width: '100%', height: '42px' }} />
          </div>
          <div className="filter-dropdowns">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="skeleton" style={{ width: '120px', height: '38px' }} />
            ))}
          </div>
        </div>
        <div className="table-wrapper">
          <table className="application-table">
            <thead>
              <tr>
                <th>Application #</th>
                <th>Student Name</th>
                <th>Branch Pref (1st)</th>
                <th>Category</th>
                <th>Quota</th>
                <th>Merit Score</th>
                <th>Status</th>
                <th>Submitted</th>
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: pagination?.page_size || 10 }).map((_, i) => renderSkeletonRow(i))}
            </tbody>
          </table>
        </div>
        <div className="table-pagination">
          <div className="pagination-left">
            <div className="skeleton" style={{ width: '180px', height: '20px' }} />
          </div>
          <div className="pagination-right">
            <div className="skeleton" style={{ width: '80px', height: '32px' }} />
            <div className="skeleton" style={{ width: '100px', height: '20px' }} />
            <div className="skeleton" style={{ width: '80px', height: '32px' }} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="application-table-container">
      {/* Filter Bar */}
      <div className="filter-bar">
        <div className="search-box">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            placeholder="Search by application # or student name..."
            value={searchValue}
            onChange={(e) => onSearch?.(e.target.value)}
            className="search-input"
          />
        </div>
        
        <div className="filter-dropdowns">
          <select 
            className="filter-select"
            value={filters.branch_id || ''}
            onChange={(e) => onFilterChange?.('branch_id', e.target.value)}
          >
            <option value="">All Branches</option>
            {branches.map(branch => (
              <option key={branch.id} value={branch.id}>{branch.name}</option>
            ))}
          </select>

          <select 
            className="filter-select"
            value={filters.quota || ''}
            onChange={(e) => onFilterChange?.('quota', e.target.value)}
          >
            {QUOTA_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <select 
            className="filter-select"
            value={filters.status || ''}
            onChange={(e) => onFilterChange?.('status', e.target.value)}
          >
            {STATUS_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <select 
            className="filter-select"
            value={filters.category || ''}
            onChange={(e) => onFilterChange?.('category', e.target.value)}
          >
            {CATEGORY_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <select 
            className="filter-select"
            value={filters.fee_status || ''}
            onChange={(e) => onFilterChange?.('fee_status', e.target.value)}
          >
            {FEE_STATUS_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Active Filter Chips */}
      {activeFilters.length > 0 && (
        <div className="active-filters">
          <span className="filters-label">Active Filters:</span>
          <div className="filter-chips">
            {activeFilters.map(([key, value]) => (
              <span key={key} className="filter-chip">
                {getFilterLabel(key, value)}
                <button 
                  className="chip-remove"
                  onClick={() => handleRemoveFilter(key)}
                >
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
          <button className="clear-all-btn" onClick={handleClearAllFilters}>
            Clear All
          </button>
        </div>
      )}

      {/* Table */}
      <div className="table-wrapper">
        <table className="application-table">
            <thead>
              <tr>
                <th 
                  className="sortable"
                  onClick={() => onSort?.('application_number')}
                >
                  Application # {getSortIcon('application_number')}
                </th>
                <th>Student Name</th>
                <th>Branch Pref (1st)</th>
                <th>Category</th>
                <th>Quota</th>
                <th 
                  className="sortable"
                  onClick={() => onSort?.('merit_score')}
                >
                  Merit Score {getSortIcon('merit_score')}
                </th>
                <th>Status</th>
                <th>Fee Status</th>
                <th 
                  className="sortable"
                  onClick={() => onSort?.('submitted_at')}
                >
                  Submitted {getSortIcon('submitted_at')}
                </th>
              </tr>
            </thead>
          <tbody>
            {applications?.length === 0 ? renderEmptyState() : (
              applications?.map((app) => (
                <tr key={app.application_id}>
                  <td className="app-number">{app.application_number}</td>
                  <td className="student-name">{app.student_name}</td>
                  <td>{getFirstBranchPreference(app.branch_preferences)}</td>
                  <td>{app.category || '-'}</td>
                  <td>{app.allocated_quota || '-'}</td>
                  <td className="merit-score">{formatMeritScore(app.merit_score)}</td>
                  <td>
                    <StatusBadge status={getStatusFromApp(app)} />
                  </td>
                  <td>
                    <div className="fee-status-cell">
                      <FeeStatusBadge feeStatus={app.fee_status || 'not_sent'} />
                      {app.fee_status === 'sent' && app.fee_instruction_sent_at && (
                        <span className="fee-sent-date">
                          {formatDate(app.fee_instruction_sent_at)}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="date">{formatDate(app.submitted_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination && (
        <div className="table-pagination">
          <div className="pagination-left">
            <span className="pagination-info">
              Showing {((pagination.page - 1) * pagination.page_size) + 1} - {Math.min(pagination.page * pagination.page_size, pagination.count)} of {pagination.count}
            </span>
            <div className="page-size-selector">
              <span>Show</span>
              <select 
                value={pagination.page_size}
                onChange={(e) => onPageSizeChange?.(parseInt(e.target.value))}
                className="page-size-select"
              >
                {PAGE_SIZE_OPTIONS.map(size => (
                  <option key={size} value={size}>{size}</option>
                ))}
              </select>
              <span>per page</span>
            </div>
          </div>
          <div className="pagination-right">
            <button
              className="pagination-btn"
              disabled={pagination.page === 1}
              onClick={() => onPageChange?.(pagination.page - 1)}
            >
              <ChevronLeft size={18} />
            </button>
            <span className="page-number">
              Page {pagination.page} of {Math.ceil(pagination.count / pagination.page_size)}
            </span>
            <button
              className="pagination-btn"
              disabled={pagination.page * pagination.page_size >= pagination.count}
              onClick={() => onPageChange?.(pagination.page + 1)}
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApplicationTable;