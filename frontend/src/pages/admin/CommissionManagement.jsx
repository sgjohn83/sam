import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminCommissionApi } from '../../services/agentApi';
import { PageHeader } from '../../components/layout/PageHeader';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { CommissionRejectModal } from '../../components/admin/CommissionRejectModal';
import { PaymentReferenceModal } from '../../components/admin/PaymentReferenceModal';
import { 
  CheckCircle2, 
  XCircle, 
  CreditCard, 
  Search, 
  Filter, 
  Loader2, 
  ChevronRight,
  TrendingUp,
  AlertCircle,
  FileCheck
} from 'lucide-react';
import { toast } from 'react-hot-toast';

export function CommissionManagement() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    status: '',
    agent: '',
    search: '',
    date_from: '',
    date_to: '',
  });

  const [selectedIds, setSelectedIds] = useState([]);
  const [rejectId, setRejectId] = useState(null);
  const [rejectReason, setRejectReason] = useState('');
  const [payId, setPayId] = useState(null);
  const [payRef, setPayRef] = useState('');
  const [bulkPayRef, setBulkPayRef] = useState('');

  // Queries
  const { data: commissions, isLoading } = useQuery({
    queryKey: ['admin-commissions', page, filters],
    queryFn: () => adminCommissionApi.getCommissions({ page, ...filters }).then(r => r.data),
  });

  const { data: agents } = useQuery({
    queryKey: ['admin-agents'],
    queryFn: () => adminCommissionApi.getAgents().then(r => r.data),
  });

  // Mutations
  const approveMutation = useMutation({
    mutationFn: (id) => adminCommissionApi.approve(id),
    onSuccess: () => {
      toast.success('Commission approved');
      queryClient.invalidateQueries(['admin-commissions']);
    }
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }) => adminCommissionApi.reject(id, reason),
    onSuccess: () => {
      toast.success('Commission rejected');
      setRejectId(null);
      setRejectReason('');
      queryClient.invalidateQueries(['admin-commissions']);
    }
  });

  const payMutation = useMutation({
    mutationFn: ({ id, ref }) => adminCommissionApi.markPaid(id, ref),
    onSuccess: () => {
      toast.success('Payment recorded');
      setPayId(null);
      setPayRef('');
      queryClient.invalidateQueries(['admin-commissions']);
    }
  });

  const bulkPayMutation = useMutation({
    mutationFn: ({ ids, ref }) => adminCommissionApi.bulkPay(ids, ref),
    onSuccess: (data) => {
      toast.success(`Successfully paid ${data.paid_count} commissions`);
      setSelectedIds([]);
      setBulkPayRef('');
      queryClient.invalidateQueries(['admin-commissions']);
    }
  });

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
    setPage(1);
  };

  const toggleSelect = (id) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  };

  const selectAllApproved = () => {
    const approvedIds = commissions?.results?.filter(r => r.status === 'approved').map(r => r.id) || [];
    if (selectedIds.length === approvedIds.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(approvedIds);
    }
  };

  const selectedTotal = commissions?.results
    ?.filter(r => selectedIds.includes(r.id))
    ?.reduce((sum, r) => sum + parseFloat(r.commission_amount), 0) || 0;

  const summary = commissions?.summary || {
    pending_amount: '0',
    approved_amount: '0',
    paid_this_month: '0'
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <PageHeader 
        title="Commission Management" 
        subtitle="Manage agent referrals, approve commissions, and record payments." 
      />

      {/* Summary Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard label="Pending Approval" value={`₹${parseFloat(summary.pending_amount).toLocaleString()}`} icon={AlertCircle} color="amber" />
        <StatCard label="Ready to Pay" value={`₹${parseFloat(summary.approved_amount).toLocaleString()}`} icon={CheckCircle2} color="blue" />
        <StatCard label="Paid This Month" value={`₹${parseFloat(summary.paid_this_month).toLocaleString()}`} icon={TrendingUp} color="emerald" />
      </div>

      {/* Bulk Action Bar */}
      {selectedIds.length > 0 && (
        <Card className="p-4 bg-blue-600 text-white flex flex-col md:flex-row items-center justify-between gap-4 sticky top-4 z-20 shadow-xl border-0 animate-in slide-in-from-top-4">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-white/20 rounded-lg">
              <FileCheck size={20} />
            </div>
            <div>
              <p className="font-bold">{selectedIds.length} Commissions Selected</p>
              <p className="text-blue-100 text-xs">Total payout: ₹{selectedTotal.toLocaleString()}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 w-full md:w-auto">
            <Input 
              placeholder="Payment Reference (e.g. Bank Ref #)"
              className="bg-white/10 border-white/20 text-white placeholder:text-blue-200 h-10 w-full md:w-64"
              value={bulkPayRef}
              onChange={(e) => setBulkPayRef(e.target.value)}
            />
            <Button 
              variant="secondary" 
              className="bg-white text-blue-600 hover:bg-blue-50 font-black h-10 whitespace-nowrap"
              disabled={!bulkPayRef || bulkPayMutation.isPending}
              onClick={() => bulkPayMutation.mutate({ ids: selectedIds, ref: bulkPayRef })}
            >
              {bulkPayMutation.isPending ? 'Processing...' : 'Mark All as Paid'}
            </Button>
          </div>
        </Card>
      )}

      {/* Filters */}
      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input 
              name="search"
              placeholder="Student or App #..." 
              className="pl-10"
              value={filters.search}
              onChange={handleFilterChange}
            />
          </div>
          <select 
            name="status"
            className="rounded-lg border-gray-200 text-sm font-medium"
            value={filters.status}
            onChange={handleFilterChange}
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="paid">Paid</option>
            <option value="rejected">Rejected</option>
          </select>
          <select 
            name="agent"
            className="rounded-lg border-gray-200 text-sm font-medium"
            value={filters.agent}
            onChange={handleFilterChange}
          >
            <option value="">All Agents</option>
            {agents?.results?.map(a => (
              <option key={a.id} value={a.id}>{a.agency_name}</option>
            ))}
          </select>
          <Input type="date" name="date_from" value={filters.date_from} onChange={handleFilterChange} />
          <Input type="date" name="date_to" value={filters.date_to} onChange={handleFilterChange} />
        </div>
      </Card>

      {/* Table */}
      <Card className="overflow-hidden border shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-[10px] uppercase tracking-wider font-black text-gray-500 bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-4">
                  <input 
                    type="checkbox" 
                    className="rounded border-gray-300 text-blue-600" 
                    onChange={selectAllApproved}
                    checked={selectedIds.length > 0 && selectedIds.length === commissions?.results?.filter(r => r.status === 'approved').length}
                  />
                </th>
                <th className="px-6 py-4">Agent & Student</th>
                <th className="px-6 py-4">Application</th>
                <th className="px-6 py-4 text-right">Fee</th>
                <th className="px-6 py-4 text-right">Commission</th>
                <th className="px-6 py-4 text-center">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y whitespace-nowrap">
              {isLoading ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center">
                    <Loader2 className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
                  </td>
                </tr>
              ) : commissions?.results?.map(record => (
                <tr key={record.id} className={`hover:bg-gray-50 transition-colors ${selectedIds.includes(record.id) ? 'bg-blue-50/50' : ''}`}>
                  <td className="px-6 py-4">
                    <input 
                      type="checkbox" 
                      className="rounded border-gray-300 text-blue-600 disabled:opacity-20"
                      disabled={record.status !== 'approved'}
                      checked={selectedIds.includes(record.id)}
                      onChange={() => toggleSelect(record.id)}
                    />
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-black text-gray-900">{record.agent_name}</div>
                    <div className="text-xs text-blue-600 font-bold">{record.student_name}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-xs font-mono font-bold text-gray-400">{record.application_number}</div>
                    <div className="text-[10px] text-gray-400">{record.branch_name || 'Verification Pending'}</div>
                  </td>
                  <td className="px-6 py-4 text-right text-xs font-bold text-gray-500">
                    ₹{parseFloat(record.fee_amount).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="font-black text-gray-900">₹{parseFloat(record.commission_amount).toLocaleString()}</div>
                    <div className="text-[10px] text-gray-400">{record.commission_rate}% rate</div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <StatusBadge status={record.status} />
                  </td>
                  <td className="px-6 py-4 text-right">
                    <ActionButtons 
                      record={record} 
                      onApprove={() => approveMutation.mutate(record.id)}
                      onReject={() => setRejectId(record.id)}
                      onPay={() => setPayId(record.id)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Modals */}
      <CommissionRejectModal 
        isOpen={!!rejectId}
        onClose={() => setRejectId(null)}
        isPending={rejectMutation.isPending}
        onConfirm={(reason) => rejectMutation.mutate({ id: rejectId, reason })}
      />

      <PaymentReferenceModal 
        isOpen={!!payId}
        onClose={() => setPayId(null)}
        isPending={payMutation.isPending}
        amount={commissions?.results?.find(r => r.id === payId)?.commission_amount}
        onConfirm={(ref) => payMutation.mutate({ id: payId, ref })}
      />
    </div>
  );
}

function StatCard({ label, value, icon: Icon, color }) {
  const colors = {
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    red: 'bg-red-50 text-red-600 border-red-100',
  };
  return (
    <Card className={`p-6 border flex items-center gap-5 ${colors[color]}`}>
      <div className="p-3 bg-white rounded-xl shadow-sm">
        <Icon size={28} />
      </div>
      <div>
        <h4 className="text-[10px] uppercase font-black tracking-widest opacity-60 mb-1">{label}</h4>
        <p className="text-2xl font-black">{value}</p>
      </div>
    </Card>
  );
}

function StatusBadge({ status }) {
  const variants = {
    pending: 'bg-amber-100 text-amber-700',
    approved: 'bg-blue-100 text-blue-700',
    paid: 'bg-emerald-100 text-emerald-700',
    rejected: 'bg-red-100 text-red-700',
  };
  return (
    <span className={`px-2 py-1 rounded text-[10px] font-black uppercase tracking-widest ${variants[status] || 'bg-gray-100'}`}>
      {status}
    </span>
  );
}

function ActionButtons({ record, onApprove, onReject, onPay }) {
  if (record.status === 'pending') {
    return (
      <div className="flex justify-end gap-2">
        <button onClick={onReject} title="Reject" className="p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
          <XCircle size={18} />
        </button>
        <button onClick={onApprove} title="Approve" className="p-2 text-emerald-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors">
          <CheckCircle2 size={18} />
        </button>
      </div>
    );
  }
  if (record.status === 'approved') {
    return (
      <button 
        onClick={onPay}
        className="text-[10px] font-black text-blue-600 hover:underline flex items-center gap-1 justify-end ml-auto"
      >
        Record Payment <ChevronRight size={14} />
      </button>
    );
  }
  if (record.status === 'paid') {
    return (
      <div className="text-right">
        <div className="text-[10px] text-gray-400 font-mono">{record.payment_reference}</div>
        <div className="text-[9px] text-emerald-500 font-bold uppercase">{new Date(record.paid_at).toLocaleDateString()}</div>
      </div>
    );
  }
  return <span className="text-[10px] text-gray-400 italic">No action</span>;
}
