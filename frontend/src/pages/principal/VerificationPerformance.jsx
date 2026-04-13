import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronUp, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { principalApi } from '../../services/principalApi';
import { PageHeader } from '../../components/layout/PageHeader';
import { StatCard } from '../../components/ui/StatCard';
import './VerificationPerformance.css';

const getQueueHealthStatus = (oldestAgeHours) => {
  if (oldestAgeHours > 48) return 'critical';
  if (oldestAgeHours > 24) return 'warning';
  return 'normal';
};

const getStaffRowHighlight = (staff) => {
  // Orange: at max capacity (3+ active claims)
  if (staff.active_claims >= 3) return 'at-capacity';
  // Yellow: no verifications this week
  if (staff.verified_this_week === 0) return 'no-activity';
  return '';
};

export function VerificationPerformance() {
  const [sortBy, setSortBy] = useState('active_claims');
  const [sortOrder, setSortOrder] = useState('desc');

  const { data, isLoading } = useQuery({
    queryKey: ['verification-performance'],
    queryFn: () => principalApi.getVerificationPerformance().then((r) => r.data),
    refetchInterval: 60000, // 1 min
  });

  const sortedStaff = useMemo(() => {
    if (!data?.staff) return [];

    const staff = [...data.staff];
    staff.sort((a, b) => {
      let aVal, bVal;

      switch (sortBy) {
        case 'name':
          aVal = a.name.toLowerCase();
          bVal = b.name.toLowerCase();
          return sortOrder === 'desc' ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
        case 'active_claims':
          aVal = a.active_claims;
          bVal = b.active_claims;
          break;
        case 'total_claimed':
          aVal = a.total_claimed;
          bVal = b.total_claimed;
          break;
        case 'verified_this_week':
          aVal = a.verified_this_week;
          bVal = b.verified_this_week;
          break;
        case 'verified_total':
          aVal = a.verified_total;
          bVal = b.verified_total;
          break;
        case 'avg_turnaround':
          aVal = a.avg_turnaround_hours || Infinity;
          bVal = b.avg_turnaround_hours || Infinity;
          break;
        default:
          return 0;
      }

      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
    });

    return staff;
  }, [data, sortBy, sortOrder]);

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

  if (isLoading) {
    return <div className="loading-overlay">Loading verification performance...</div>;
  }

  const queueStatus = getQueueHealthStatus(data?.queue_health?.oldest_age_hours || 0);
  const hasAlerts =
    (data?.queue_health?.unclaimed_in_queue || 0) > 5 ||
    (data?.queue_health?.oldest_age_hours || 0) > 48 ||
    sortedStaff.some((s) => s.active_claims >= 3);

  return (
    <div className="verification-performance-page">
      <PageHeader
        title="Verification Performance"
        subtitle="Staff capacity, queue health, and turnaround tracking"
      />

      {/* Queue Health Summary */}
      <section className="stats-grid">
        <StatCard
          title="Total Pending"
          value={data?.queue_health?.total_pending_verification || 0}
          icon={Clock}
          color="info"
        />
        <StatCard
          title="Unclaimed Applications"
          value={data?.queue_health?.unclaimed_in_queue || 0}
          icon={AlertCircle}
          color={queueStatus === 'critical' ? 'danger' : queueStatus === 'warning' ? 'warning' : 'success'}
        />
        <StatCard
          title="Oldest Pending (hours)"
          value={Math.round(data?.queue_health?.oldest_age_hours || 0)}
          icon={Clock}
          color={queueStatus === 'critical' ? 'danger' : queueStatus === 'warning' ? 'warning' : 'success'}
        />
        <StatCard
          title="Active Staff"
          value={data?.staff?.length || 0}
          icon={CheckCircle}
          color="primary"
        />
      </section>

      {/* Alerts */}
      {hasAlerts && (
        <section className="alerts-section">
          <div className="alert-header">
            <AlertCircle size={18} />
            <span>Queue Health Alerts</span>
          </div>
          <div className="alert-list">
            {(data?.queue_health?.unclaimed_in_queue || 0) > 5 && (
              <div className="alert-item warning">
                <span className="alert-icon">⚠</span>
                <span>
                  {data.queue_health.unclaimed_in_queue} applications waiting to be claimed by staff
                </span>
              </div>
            )}
            {(data?.queue_health?.oldest_age_hours || 0) > 48 && (
              <div className="alert-item critical">
                <span className="alert-icon">🔴</span>
                <span>
                  Application pending for {Math.round(data.queue_health.oldest_age_hours)} hours — SLA
                  may be breached
                </span>
              </div>
            )}
            {sortedStaff.some((s) => s.active_claims >= 3) && (
              <div className="alert-item warning">
                <span className="alert-icon">⚠</span>
                <span>{sortedStaff.filter((s) => s.active_claims >= 3).length} staff members at max capacity</span>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Staff Performance Table */}
      <section className="staff-table-container">
        <table className="staff-table">
          <thead>
            <tr>
              <th>
                <button className="sort-header" onClick={() => handleSort('name')}>
                  Staff Name <SortIcon column="name" />
                </button>
              </th>
              <th>Email</th>
              <th>
                <button className="sort-header" onClick={() => handleSort('active_claims')}>
                  Active Claims <SortIcon column="active_claims" />
                </button>
              </th>
              <th>
                <button className="sort-header" onClick={() => handleSort('total_claimed')}>
                  Total Claimed <SortIcon column="total_claimed" />
                </button>
              </th>
              <th>
                <button className="sort-header" onClick={() => handleSort('verified_this_week')}>
                  Verified This Week <SortIcon column="verified_this_week" />
                </button>
              </th>
              <th>
                <button className="sort-header" onClick={() => handleSort('verified_total')}>
                  Total Verified <SortIcon column="verified_total" />
                </button>
              </th>
              <th>
                <button className="sort-header" onClick={() => handleSort('avg_turnaround')}>
                  Avg Turnaround (hrs) <SortIcon column="avg_turnaround" />
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedStaff.map((staff) => {
              const highlightClass = getStaffRowHighlight(staff);
              return (
                <tr key={staff.user_id} className={`staff-row ${highlightClass}`}>
                  <td className="staff-name">{staff.name}</td>
                  <td className="staff-email">{staff.email}</td>
                  <td className="number">
                    <div className="capacity-cell">
                      <span>{staff.active_claims}</span>
                      {staff.active_claims >= 3 && <span className="capacity-badge">MAX</span>}
                    </div>
                  </td>
                  <td className="number">{staff.total_claimed}</td>
                  <td className="number">{staff.verified_this_week}</td>
                  <td className="number">{staff.verified_total}</td>
                  <td className="number">
                    {staff.avg_turnaround_hours ? Math.round(staff.avg_turnaround_hours) : '—'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {sortedStaff.length === 0 && (
          <div className="empty-state">
            <p>No staff data available</p>
          </div>
        )}
      </section>

      {/* Legend */}
      <section className="legend-section">
        <div className="legend-title">Highlight Legend</div>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-color yellow"></div>
            <span>No verifications this week — staff may need assignment</span>
          </div>
          <div className="legend-item">
            <div className="legend-color orange"></div>
            <span>At maximum capacity (3+ active claims) — cannot accept new assignments</span>
          </div>
        </div>
      </section>
    </div>
  );
}
