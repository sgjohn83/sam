import React, { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DashboardStats } from '../../components/officer/DashboardStats';
import { ApplicationTable } from '../../components/officer/ApplicationTable';
import { officerApi } from '../../services/officerApi';
import api from '../../services/api';
import './OfficerDashboard.css';
import { AlertTriangle, RefreshCw } from 'lucide-react';

const ErrorFallback = ({ message, onRetry }) => (
  <div className="error-boundary">
    <div className="error-content">
      <AlertTriangle size={48} className="error-icon" />
      <h3>Something went wrong</h3>
      <p>{message || 'Failed to load data. Please try again.'}</p>
      <button className="retry-btn" onClick={onRetry}>
        <RefreshCw size={16} />
        Try Again
      </button>
    </div>
  </div>
);

const LoadingSkeleton = () => (
  <div className="loading-skeleton">
    <div className="skeleton-grid">
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="skeleton-card">
          <div className="skeleton skeleton-text" style={{ width: '60%', height: '16px' }} />
          <div className="skeleton skeleton-text" style={{ width: '80%', height: '32px', marginTop: '8px' }} />
        </div>
      ))}
    </div>
  </div>
);

const EmptyApplications = ({ hasFilters }) => (
  <div className="empty-applications">
    <div className="empty-content">
      <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
        <rect width="80" height="80" rx="16" fill="#F3F4F6" />
        <path d="M24 32h32M24 40h24M24 48h16" stroke="#9CA3AF" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <h3>No Applications</h3>
      <p>{hasFilters ? 'No applications match your filters.' : 'No applications yet.'}</p>
    </div>
  </div>
);

export const OfficerDashboard = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('merit_score');
  const [sortOrder, setSortOrder] = useState('desc');
  const [filters, setFilters] = useState({
    branch_id: '',
    quota: '',
    status: '',
    category: '',
    domicile_state: '',
    fee_status: '',
  });

  // Fetch dashboard stats
  const { data: stats, isLoading: statsLoading, error: statsError, refetch: refetchStats } = useQuery({
    queryKey: ['officer-dashboard-stats'],
    queryFn: () => officerApi.getDashboardStats().then(res => res.data),
    refetchInterval: 60000,
    retry: 1,
  });

  // Fetch branches
  const { data: branchesData, error: branchesError, refetch: refetchBranches } = useQuery({
    queryKey: ['branches'],
    queryFn: () => api.get('/branches/').then(res => res.data),
    retry: 1,
  });

  // Fetch applications
  const { data: applicationsData, isLoading: appsLoading, error: appsError, refetch: refetchApps } = useQuery({
    queryKey: ['officer-applications', page, pageSize, search, sortBy, sortOrder, filters],
    queryFn: () => officerApi.getApplications({
      page,
      page_size: pageSize,
      search: search || undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
      branch_id: filters.branch_id || undefined,
      quota: filters.quota || undefined,
      status: filters.status || undefined,
      category: filters.category || undefined,
      domicile_state: filters.domicile_state || undefined,
      fee_status: filters.fee_status || undefined,
    }).then(res => res.data),
    retry: 1,
  });

  // Determine error state
  const error = statsError || branchesError || appsError ? 'Failed to load dashboard data' : null;

  // Clear error on retry
  const handleRetry = () => {
    refetchStats();
    refetchBranches();
    refetchApps();
  };

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const filtersRef = React.useRef(filters);
  filtersRef.current = filters;

  useEffect(() => {
    const hasChanged = Object.keys(filters).some(
      key => filters[key] !== filtersRef.current[key]
    );
    if (hasChanged) {
      setPage(1);
    }
  }, [filters.branch_id, filters.quota, filters.status, filters.category, filters.domicile_state, filters.fee_status]);

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const handlePageChange = (newPage) => {
    setPage(newPage);
  };

  const handlePageSizeChange = (newSize) => {
    setPageSize(newSize);
    setPage(1);
  };

  const handleFilterChange = useCallback((key, value) => {
    if (key === null) {
      setFilters({
        branch_id: '',
        quota: '',
        status: '',
        category: '',
        domicile_state: '',
        fee_status: '',
      });
    } else {
      setFilters(prev => ({
        ...prev,
        [key]: value,
      }));
    }
  }, []);

  const branches = branchesData?.results || branchesData || [];

  if (error) {
    return (
      <div className="officer-dashboard">
        <div className="dashboard-header">
          <h1>Admission Dashboard</h1>
          <p className="dashboard-subtitle">Manage and track student admissions</p>
        </div>
        <ErrorFallback message={error} onRetry={handleRetry} />
      </div>
    );
  }

  return (
    <div className="officer-dashboard">
      <div className="dashboard-header">
        <h1>Admission Dashboard</h1>
        <p className="dashboard-subtitle">Manage and track student admissions</p>
      </div>

      {statsLoading ? <LoadingSkeleton /> : <DashboardStats stats={stats} isLoading={statsLoading} />}

      <div className="applications-section">
        <h2>Applications</h2>
        <ApplicationTable
          applications={applicationsData?.results}
          isLoading={appsLoading}
          pagination={applicationsData ? {
            page: applicationsData.page,
            page_size: applicationsData.page_size,
            count: applicationsData.count,
          } : null}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
          onSort={handleSort}
          sortBy={sortBy}
          sortOrder={sortOrder}
          onSearch={setSearch}
          searchValue={search}
          filters={filters}
          onFilterChange={handleFilterChange}
          branches={branches}
        />
      </div>
    </div>
  );
};

export default OfficerDashboard;