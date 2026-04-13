import React from 'react';
import { 
  CheckCircle, 
  Lock, 
  Users, 
  Clock,
  TrendingUp,
  Award,
  FileCheck,
  AlertCircle
} from 'lucide-react';
import './DashboardStats.css';

const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
  <div className={`stat-card stat-card-${color}`}>
    <div className="stat-icon">
      <Icon size={24} />
    </div>
    <div className="stat-content">
      <span className="stat-value">{value ?? '-'}</span>
      <span className="stat-title">{title}</span>
      {subtitle && <span className="stat-subtitle">{subtitle}</span>}
    </div>
  </div>
);

export const DashboardStats = ({ stats, isLoading }) => {
  if (isLoading) {
    return (
      <div className="dashboard-stats">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="stat-card stat-card-skeleton">
            <div className="skeleton-icon" />
            <div className="skeleton-content">
              <div className="skeleton-value" />
              <div className="skeleton-title" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const byStatus = stats?.by_status || {};
  
  return (
    <div className="dashboard-stats">
      <StatCard
        title="Total Verified"
        value={byStatus.verified || 0}
        icon={CheckCircle}
        color="blue"
        subtitle="Ready for allocation"
      />
      <StatCard
        title="Locked"
        value={byStatus.locked || 0}
        icon={Lock}
        color="gray"
        subtitle="Under review"
      />
      <StatCard
        title="Allocated"
        value={byStatus.allocated || 0}
        icon={Users}
        color="orange"
        subtitle="Seat assigned"
      />
      <StatCard
        title="Admitted"
        value={byStatus.admitted || 0}
        icon={Award}
        color="green"
        subtitle="Completed admission"
      />
      <StatCard
        title="Fee Pending"
        value={byStatus.fee_pending || 0}
        icon={Clock}
        color="yellow"
        subtitle="Awaiting payment"
      />
      <StatCard
        title="Rejected"
        value={byStatus.rejected || 0}
        icon={AlertCircle}
        color="red"
        subtitle="Not eligible"
      />
    </div>
  );
};

export default DashboardStats;