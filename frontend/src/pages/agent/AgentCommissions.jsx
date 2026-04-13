import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { agentApi } from '../../services/agentApi';
import { PageHeader } from '../../components/layout/PageHeader';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { IndianRupee, Filter, Loader2, CheckCircle, AlertCircle, TrendingUp } from 'lucide-react';

export function AgentCommissions() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');

  const { data, isLoading, isPlaceholderData } = useQuery({
    queryKey: ['agent-commissions', page, status],
    queryFn: () => agentApi.getCommissions({ page, status }).then(r => r.data),
    placeholderData: (previous) => previous,
  });

  const handleStatusChange = (e) => {
    setStatus(e.target.value);
    setPage(1);
  };

  const summary = data?.summary || {
    pending_amount: '0',
    pending_count: 0,
    approved_amount: '0',
    paid_amount: '0',
    total_earned: '0'
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <PageHeader 
        title="Commissions" 
        subtitle="Track your earnings and payment status for student referrals" 
      />

      {/* Summary Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard 
          label="Pending Activation" 
          value={`₹${parseFloat(summary.pending_amount).toLocaleString()}`} 
          subValue={`${summary.pending_count} students`}
          icon={AlertCircle}
          color="amber"
          pulse={summary.pending_count > 0}
        />
        <SummaryCard 
          label="Approved" 
          value={`₹${parseFloat(summary.approved_amount).toLocaleString()}`} 
          icon={CheckCircle}
          color="blue"
        />
        <SummaryCard 
          label="Total Paid" 
          value={`₹${parseFloat(summary.paid_amount).toLocaleString()}`} 
          icon={TrendingUp}
          color="emerald"
        />
        <SummaryCard 
          label="Lifetime Earnings" 
          value={`₹${parseFloat(summary.total_earned).toLocaleString()}`} 
          icon={IndianRupee}
          color="indigo"
          isTotal
        />
      </div>

      <Card className="p-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Filter size={18} className="text-gray-400" />
          <span className="text-sm font-bold text-gray-700">Filter by Status:</span>
          <select 
            className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2"
            value={status}
            onChange={handleStatusChange}
          >
            <option value="">All Payments</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="paid">Paid</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </Card>

      <Card className="overflow-hidden border shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-gray-500">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-4">Student</th>
                <th className="px-6 py-4">App #</th>
                <th className="px-6 py-4 text-right">Fee Paid</th>
                <th className="px-6 py-4 text-center">Rate</th>
                <th className="px-6 py-4 text-right">Commission</th>
                <th className="px-6 py-4 text-center">Status</th>
                <th className="px-6 py-4">Paid Date</th>
              </tr>
            </thead>
            <tbody className="divide-y whitespace-nowrap">
              {isLoading && !isPlaceholderData ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
                      <p className="text-gray-400 font-medium">Loading records...</p>
                    </div>
                  </td>
                </tr>
              ) : data?.results?.length > 0 ? (
                data.results.map((record) => (
                  <tr key={record.id} className="bg-white hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-bold text-gray-900">{record.student_name}</div>
                      <div className="text-xs text-gray-400">{record.branch_name || '—'}</div>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs">{record.application_number}</td>
                    <td className="px-6 py-4 text-right font-medium">
                      ₹{parseFloat(record.fee_amount).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className="bg-gray-100 px-2 py-0.5 rounded text-[10px] font-bold text-gray-600">
                        {record.commission_rate}%
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right font-bold text-gray-900">
                      ₹{parseFloat(record.commission_amount).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <CommissionBadge status={record.status} />
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {record.paid_at 
                        ? new Date(record.paid_at).toLocaleDateString('en-IN', {
                            day: '2-digit', month: 'short', year: 'numeric'
                          })
                        : '—'
                      }
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center text-gray-400 italic">
                    No commission records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination same as student list */}
        {data?.count > 0 && (
          <div className="px-6 py-4 bg-gray-50 border-t flex items-center justify-between">
            <span className="text-sm text-gray-700">
              Showing records <span className="font-bold">{(page-1)*20 + 1}</span> to <span className="font-bold">{Math.min(page*20, data.count)}</span>
            </span>
            <div className="flex gap-2">
              <button
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                className="px-4 py-1.5 bg-white border border-gray-300 rounded-lg text-sm font-bold disabled:opacity-50 hover:bg-gray-50 transition-colors"
              >
                Previous
              </button>
              <button
                disabled={page * 20 >= data.count}
                onClick={() => setPage(p => p + 1)}
                className="px-4 py-1.5 bg-white border border-gray-300 rounded-lg text-sm font-bold disabled:opacity-50 hover:bg-gray-50 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

function SummaryCard({ label, value, subValue, icon: Icon, color, pulse = false, isTotal = false }) {
  const colorMap = {
    amber: 'from-amber-50 to-orange-50 text-amber-600 border-amber-100',
    blue: 'from-blue-50 to-indigo-50 text-blue-600 border-blue-100',
    emerald: 'from-emerald-50 to-teal-50 text-emerald-600 border-emerald-100',
    indigo: 'from-indigo-600 to-blue-700 text-white border-transparent shadow-md'
  };

  return (
    <div className={`p-4 rounded-xl border flex items-center gap-4 bg-gradient-to-br ${colorMap[color]}`}>
      <div className={`p-3 rounded-lg ${isTotal ? 'bg-white/10' : 'bg-white shadow-sm'} ${pulse ? 'animate-pulse' : ''}`}>
        <Icon size={24} />
      </div>
      <div>
        <p className={`text-[10px] uppercase tracking-wider font-bold ${isTotal ? 'text-blue-100' : 'text-gray-500'}`}>
          {label}
        </p>
        <p className="text-xl font-black">{value}</p>
        {subValue && <p className="text-[10px] mt-0.5 opacity-80">{subValue}</p>}
      </div>
    </div>
  );
}

function CommissionBadge({ status }) {
  const map = {
    'pending': { variant: 'orange', label: 'Pending' },
    'approved': { variant: 'primary', label: 'Approved' },
    'paid': { variant: 'success', label: 'Paid ✓' },
    'rejected': { variant: 'danger', label: 'Rejected' },
  };
  const { variant, label } = map[status] || { variant: 'neutral', label: status };
  return <Badge variant={variant}>{label}</Badge>;
}
