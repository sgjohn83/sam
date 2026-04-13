import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { agentApi } from '../../services/agentApi';
import { StatCard } from '../../components/ui/StatCard';
import { PageHeader } from '../../components/layout/PageHeader';
import { 
  Users, 
  GraduationCap, 
  Clock, 
  IndianRupee, 
  ArrowRight,
  ChevronRight,
  ExternalLink
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Cell 
} from 'recharts';
import { Link } from 'react-router-dom';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';

export function AgentDashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['agent-dashboard'],
    queryFn: () => agentApi.getDashboard().then(r => r.data),
    refetchInterval: 60000,
  });

  const { data: recentStudents } = useQuery({
    queryKey: ['agent-recent-students'],
    queryFn: () => agentApi.getStudents({ page: 1, page_size: 5 }).then(r => r.data),
  });

  const { data: recentCommissions } = useQuery({
    queryKey: ['agent-recent-commissions'],
    queryFn: () => agentApi.getCommissions({ page: 1, page_size: 5 }).then(r => r.data),
  });

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-500 font-medium">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <h3 className="text-red-800 font-bold text-lg">Failed to load dashboard</h3>
          <p className="text-red-600 mt-1">Please try refreshing the page or contact support.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto">
      <PageHeader
        title={`Welcome back, ${data.agent.agency_name || 'Partner'}`}
        subtitle={data.agent.is_verified ? 'Authorized Admission Partner' : 'Verification in Progress'}
      />

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Students Referred" 
          value={data.students.total_referred} 
          icon={Users} 
          color="primary" 
        />
        <StatCard 
          title="Successfully Admitted" 
          value={data.students.admitted} 
          icon={GraduationCap} 
          color="success" 
        />
        <StatCard 
          title="Pending Commission" 
          value={`₹${parseFloat(data.commission.pending_amount).toLocaleString()}`} 
          icon={Clock} 
          color="warning" 
        />
        <StatCard 
          title="Paid Commission" 
          value={`₹${parseFloat(data.commission.paid_amount).toLocaleString()}`} 
          icon={IndianRupee} 
          color="success" 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Funnel Chart */}
        <Card className="lg:col-span-2 p-6 flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-gray-900">Application Pipeline</h3>
            <Link to="/agent/students" className="text-sm text-blue-600 hover:underline flex items-center gap-1 font-medium">
              View All <ChevronRight size={14} />
            </Link>
          </div>
          <div className="h-[350px] w-full">
            <ApplicationFunnel data={data.students} />
          </div>
        </Card>

        {/* Quick Actions / Notices */}
        <div className="space-y-6">
          <Card className="p-6 bg-gradient-to-br from-blue-600 to-indigo-700 text-white border-0 shadow-lg relative overflow-hidden">
            <div className="relative z-10">
              <h3 className="text-xl font-bold mb-2">Grow Your Network</h3>
              <p className="text-blue-100 text-sm mb-6 leading-relaxed">
                Start a new application for a student and earn commission on successful admission.
              </p>
              <Link 
                to="/agent/students/register" 
                className="inline-flex items-center gap-2 bg-white text-blue-700 px-5 py-2.5 rounded-lg font-bold shadow-sm hover:bg-blue-50 transition-colors"
              >
                Register New Student <ArrowRight size={18} />
              </Link>
            </div>
            {/* Abstract Background circles */}
            <div className="absolute -bottom-6 -right-6 w-32 h-32 bg-white/10 rounded-full blur-3xl"></div>
            <div className="absolute -top-12 -left-12 w-48 h-48 bg-white/5 rounded-full blur-3xl"></div>
          </Card>

          <Card className="p-6">
            <h3 className="font-bold text-gray-900 mb-4">Verification Status</h3>
            <div className="flex items-start gap-4">
              <div className={`p-2 rounded-full ${data.agent.is_verified ? 'bg-green-100 text-green-600' : 'bg-amber-100 text-amber-600'}`}>
                {data.agent.is_verified ? <GraduationCap size={20} /> : <Clock size={20} />}
              </div>
              <div className="flex-1">
                <p className="text-sm font-bold text-gray-900">
                  {data.agent.is_verified ? 'Account Fully Verified' : 'Account Under Review'}
                </p>
                <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                  {data.agent.is_verified 
                    ? 'Your account is verified. You can now process unlimited student referrals and track commissions.' 
                    : 'Our team is verifying your agency documents. You can still register students in the meantime.'}
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Students */}
        <Card className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-gray-900">Recent Students</h3>
            <Link to="/agent/students" className="text-blue-600 hover:text-blue-700">
              <ExternalLink size={18} />
            </Link>
          </div>
          <div className="space-y-4">
            {recentStudents?.results?.length > 0 ? (
              recentStudents.results.map(student => (
                <div key={student.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 border border-transparent hover:border-gray-100 transition-all">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-gray-100 rounded-full flex items-center justify-center font-bold text-gray-600">
                      {student.full_name.charAt(0)}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-gray-900">{student.full_name}</p>
                      <p className="text-xs text-gray-500">{student.application_number || 'No Application'}</p>
                    </div>
                  </div>
                  <Badge variant={getStatusVariant(student.status)}>
                    {student.status || 'Draft'}
                  </Badge>
                </div>
              ))
            ) : (
              <p className="text-center py-8 text-gray-400 italic">No students registered yet.</p>
            )}
          </div>
        </Card>

        {/* Recent Commissions */}
        <Card className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-gray-900">Commission Activity</h3>
            <Link to="/agent/commissions" className="text-blue-600 hover:text-blue-700">
              <ExternalLink size={18} />
            </Link>
          </div>
          <div className="space-y-4">
            {recentCommissions?.results?.length > 0 ? (
              recentCommissions.results.map(record => (
                <div key={record.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 border border-transparent hover:border-gray-100 transition-all">
                  <div className="flex items-center gap-3">
                    <div className={`w-9 h-9 rounded-full flex items-center justify-center font-bold ${getCommissionVariant(record.status).icon}`}>
                      <IndianRupee size={16} />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-gray-900">₹{parseFloat(record.commission_amount).toLocaleString()}</p>
                      <p className="text-xs text-gray-500">{record.student_name}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-xs font-bold ${getCommissionVariant(record.status).text}`}>
                      {record.status.toUpperCase()}
                    </p>
                    <p className="text-[10px] text-gray-400">{new Date(record.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-center py-8 text-gray-400 italic">No commission records yet.</p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

function ApplicationFunnel({ data }) {
  const chartData = [
    { name: 'Draft', count: data.draft, color: '#94a3b8' },
    { name: 'Submitted', count: data.submitted, color: '#3b82f6' },
    { name: 'Under Verification', count: data.under_verification, color: '#fbbf24' },
    { name: 'Verified', count: data.verified, color: '#10b981' },
    { name: 'Seat Allocated', count: data.seat_allocated, color: '#8b5cf6' },
    { name: 'Fee Pending', count: data.fee_pending, color: '#f43f5e' },
    { name: 'Admitted', count: data.admitted, color: '#059669' },
  ].filter(item => item.count >= 0);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        layout="vertical"
        data={chartData}
        margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#f1f5f9" />
        <XAxis type="number" hide />
        <YAxis 
          type="category" 
          dataKey="name" 
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 12, fontWeight: 500, fill: '#64748b' }}
          width={120}
        />
        <Tooltip 
          cursor={{ fill: '#f8fafc' }}
          contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
        />
        <Bar dataKey="count" barSize={32} radius={[0, 6, 6, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function getStatusVariant(status) {
  const map = {
    'draft': 'neutral',
    'submitted': 'info',
    'under_verification': 'warning',
    'verified': 'success',
    'seat_allocated': 'primary',
    'fee_pending': 'danger',
    'admitted': 'success',
    'rejected': 'danger',
  };
  return map[status] || 'neutral';
}

function getCommissionVariant(status) {
  const map = {
    'pending': { icon: 'bg-amber-100 text-amber-600', text: 'text-amber-600' },
    'approved': { icon: 'bg-blue-100 text-blue-600', text: 'text-blue-600' },
    'paid': { icon: 'bg-green-100 text-green-600', text: 'text-green-600' },
    'rejected': { icon: 'bg-red-100 text-red-600', text: 'text-red-600' },
  };
  return map[status] || { icon: 'bg-gray-100 text-gray-600', text: 'text-gray-600' };
}
