import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronUp, TrendingUp, Users, Award, DollarSign } from 'lucide-react';
import { principalApi } from '../../services/principalApi';
import { PageHeader } from '../../components/layout/PageHeader';
import { StatCard } from '../../components/ui/StatCard';
import './AgentPerformance.css';

const getConversionColor = (rate) => {
  if (rate > 50) return '#059669'; // green
  if (rate >= 25) return '#D97706'; // yellow
  return '#DC2626'; // red
};

export function AgentPerformance() {
  const [sortBy, setSortBy] = useState('admitted'); // admitted, referred, conversion, commission
  const [sortOrder, setSortOrder] = useState('desc');
  const [expandedAgentId, setExpandedAgentId] = useState(null);

  const { data, isLoading } = useQuery({
    queryKey: ['agent-performance'],
    queryFn: () => principalApi.getAgentPerformance().then((r) => r.data),
    refetchInterval: 60000, // 1 min
  });

  const sortedAgents = useMemo(() => {
    if (!data?.agents) return [];

    const agents = [...data.agents];
    agents.sort((a, b) => {
      let aVal, bVal;

      switch (sortBy) {
        case 'admitted':
          aVal = a.admitted;
          bVal = b.admitted;
          break;
        case 'referred':
          aVal = a.referred;
          bVal = b.referred;
          break;
        case 'conversion':
          aVal = a.conversion_rate;
          bVal = b.conversion_rate;
          break;
        case 'commission':
          aVal = parseFloat(a.commission_paid);
          bVal = parseFloat(b.commission_paid);
          break;
        default:
          return 0;
      }

      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
    });

    return agents;
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
    return <div className="loading-overlay">Loading agent performance...</div>;
  }

  const totalCommissionPaid = data?.agents?.reduce(
    (sum, a) => sum + parseFloat(a.commission_paid || 0),
    0,
  ) || 0;

  return (
    <div className="agent-performance-page">
      <PageHeader
        title="Agent Performance"
        subtitle="Commission earnings and student admission tracking"
      />

      {/* Summary Cards */}
      <section className="stats-grid">
        <StatCard
          title="Total Active Agents"
          value={data?.summary?.total_agents || 0}
          icon={Users}
          color="primary"
        />
        <StatCard
          title="Total Referred"
          value={data?.summary?.total_referred || 0}
          icon={TrendingUp}
          color="info"
        />
        <StatCard
          title="Total Admitted (via Agents)"
          value={data?.summary?.total_admitted_via_agents || 0}
          icon={Award}
          color="success"
        />
        <StatCard
          title="Total Commission Paid"
          value={`₹${totalCommissionPaid.toLocaleString('en-IN', {
            minimumFractionDigits: 0,
          })}`}
          icon={DollarSign}
          color="warning"
        />
      </section>

      {/* Agent Table */}
      <section className="agent-table-container">
        <table className="agent-table">
          <thead>
            <tr>
              <th></th>
              <th>Agent Name</th>
              <th>Email</th>
              <th>
                <button
                  className="sort-header"
                  onClick={() => handleSort('referred')}
                >
                  Referred <SortIcon column="referred" />
                </button>
              </th>
              <th>
                <button
                  className="sort-header"
                  onClick={() => handleSort('admitted')}
                >
                  Admitted <SortIcon column="admitted" />
                </button>
              </th>
              <th>Pending</th>
              <th>Rejected</th>
              <th>
                <button
                  className="sort-header"
                  onClick={() => handleSort('conversion')}
                >
                  Conversion <SortIcon column="conversion" />
                </button>
              </th>
              <th>
                <button
                  className="sort-header"
                  onClick={() => handleSort('commission')}
                >
                  Comm. Paid <SortIcon column="commission" />
                </button>
              </th>
              <th>Pending</th>
            </tr>
          </thead>
          <tbody>
            {sortedAgents.map((agent) => (
              <React.Fragment key={agent.agent_id}>
                <tr className="agent-row">
                  <td className="expand-cell">
                    <button
                      className="expand-btn"
                      onClick={() =>
                        setExpandedAgentId(
                          expandedAgentId === agent.agent_id ? null : agent.agent_id,
                        )
                      }
                      title="View student breakdown"
                    >
                      {expandedAgentId === agent.agent_id ? (
                        <ChevronUp size={18} />
                      ) : (
                        <ChevronDown size={18} />
                      )}
                    </button>
                  </td>
                  <td className="agent-name">
                    <div>
                      <strong>{agent.name}</strong>
                      {!agent.is_verified && (
                        <span className="unverified-badge">Unverified</span>
                      )}
                    </div>
                  </td>
                  <td>{agent.email}</td>
                  <td className="number">{agent.referred}</td>
                  <td className="number">{agent.admitted}</td>
                  <td className="number">{agent.pending}</td>
                  <td className="number">{agent.rejected}</td>
                  <td>
                    <div
                      className="conversion-rate"
                      style={{
                        backgroundColor: getConversionColor(agent.conversion_rate),
                      }}
                    >
                      {agent.conversion_rate.toFixed(1)}%
                    </div>
                  </td>
                  <td className="currency">
                    ₹{parseFloat(agent.commission_paid).toLocaleString('en-IN')}
                  </td>
                  <td className="currency">
                    ₹{parseFloat(agent.commission_pending).toLocaleString('en-IN')}
                  </td>
                </tr>

                {/* Expanded Student List */}
                {expandedAgentId === agent.agent_id && (
                  <tr className="expanded-row">
                    <td colSpan="10">
                      <AgentStudentSummary agentId={agent.agent_id} />
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>

        {sortedAgents.length === 0 && (
          <div className="empty-state">
            <p>No agents found</p>
          </div>
        )}
      </section>
    </div>
  );
}

/**
 * Expandable panel showing an agent's student status breakdown.
 * Shows counts of students at each application stage.
 */
function AgentStudentSummary({ agentId }) {
  const statusConfig = [
    { key: 'draft', label: 'Draft', color: '#9CA3AF' },
    { key: 'submitted', label: 'Submitted', color: '#3B82F6' },
    { key: 'under_verification', label: 'Verifying', color: '#F59E0B' },
    { key: 'verified', label: 'Verified', color: '#10B981' },
    { key: 'seat_allocated', label: 'Seat Alloc.', color: '#8B5CF6' },
    { key: 'fee_pending', label: 'Fee Due', color: '#F97316' },
    { key: 'admitted', label: 'Admitted', color: '#059669' },
    { key: 'rejected', label: 'Rejected', color: '#DC2626' },
  ];

  // In a real implementation, fetch per-agent student breakdown
  // For now showing placeholder structure
  return (
    <div className="agent-student-summary">
      <h4>Student Status Breakdown</h4>
      <div className="status-grid">
        {statusConfig.map(({ key, label, color }) => (
          <div key={key} className="status-item">
            <div className="status-dot" style={{ backgroundColor: color }}></div>
            <span className="status-label">{label}</span>
            <span className="status-count">—</span>
          </div>
        ))}
      </div>
      <p className="summary-note">
        Detailed student breakdown for this agent would load here with full status tracking.
      </p>
    </div>
  );
}
