import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '../../components/layout/PageHeader';
import { principalApi } from '../../services/principalApi';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from 'recharts';
import {
  FileText,
  GraduationCap,
  BookMarked,
  IndianRupee,
  Timer,
} from 'lucide-react';

const REFRESH_INTERVAL = 60000;
const PERIODS = ['daily', 'weekly', 'monthly'];

export function PrincipalDashboard() {
  const [period, setPeriod] = useState('daily');

  const { data: admissionStats, isLoading: loadingAdmission } = useQuery({
    queryKey: ['principal-admission-stats'],
    queryFn: () => principalApi.getAdmissionStats().then((r) => r.data),
    refetchInterval: REFRESH_INTERVAL,
  });

  const { data: seatStats, isLoading: loadingSeats } = useQuery({
    queryKey: ['principal-seat-stats'],
    queryFn: () => principalApi.getSeatStats().then((r) => r.data),
    refetchInterval: REFRESH_INTERVAL,
  });

  const { data: revenueStats, isLoading: loadingRevenue } = useQuery({
    queryKey: ['principal-revenue-stats'],
    queryFn: () => principalApi.getRevenueStats().then((r) => r.data),
    refetchInterval: REFRESH_INTERVAL,
  });

  const { data: trend, isLoading: loadingTrend } = useQuery({
    queryKey: ['admission-trend', period],
    queryFn: () => principalApi.getAdmissionTrend({ period, days: 90 }).then((r) => r.data),
    refetchInterval: REFRESH_INTERVAL,
  });

  const mergedTrend = useMemo(() => mergeTrendData(trend, period), [trend, period]);
  const funnelData = useMemo(
    () => buildFunnelData(admissionStats?.status_breakdown),
    [admissionStats?.status_breakdown]
  );
  const seatFillData = useMemo(() => buildSeatFillData(seatStats?.by_branch), [seatStats?.by_branch]);

  const loading = loadingAdmission || loadingSeats || loadingRevenue;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <PageHeader title="Principal Dashboard" />

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
        <MetricCard
          title="Total Applications"
          value={toNumber(admissionStats?.total_applications).toLocaleString()}
          subtitle={`Today: ${toNumber(admissionStats?.today).toLocaleString()}`}
          icon={FileText}
          loading={loading}
        />
        <MetricCard
          title="Admitted"
          value={toNumber(admissionStats?.funnel?.admitted).toLocaleString()}
          subtitle={`Conversion: ${toNumber(admissionStats?.funnel?.conversion_rate).toFixed(1)}%`}
          icon={GraduationCap}
          loading={loading}
        />
        <MetricCard
          title="Seats Filled"
          value={toNumber(seatStats?.allocated_seats).toLocaleString()}
          subtitle={`Fill: ${toNumber(seatStats?.fill_percentage).toFixed(1)}%`}
          icon={BookMarked}
          loading={loading}
        />
        <MetricCard
          title="Revenue Collected"
          value={formatINR(revenueStats?.collected?.amount)}
          subtitle={`Pending: ${formatINR(revenueStats?.pending?.amount)}`}
          icon={IndianRupee}
          loading={loading}
        />
        <MetricCard
          title="Avg Processing Time"
          value={admissionStats?.avg_processing_days != null ? `${admissionStats.avg_processing_days} days` : '--'}
          subtitle="Submitted to admitted"
          icon={Timer}
          loading={loading}
        />
      </div>

      <div className="bg-white border rounded-lg shadow p-5">
        <AdmissionTrendChart
          period={period}
          onPeriodChange={setPeriod}
          data={mergedTrend}
          loading={loadingTrend}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="bg-white border rounded-lg shadow p-5">
          <div className="mb-4">
            <h3 className="text-lg font-bold text-gray-900">Application Funnel</h3>
            <p className="text-sm text-gray-500">Overall application flow by status</p>
          </div>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              layout="vertical"
              data={funnelData}
              margin={{ top: 8, right: 12, left: 12, bottom: 8 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal vertical={false} stroke="#f1f5f9" />
              <XAxis type="number" hide />
              <YAxis
                type="category"
                dataKey="name"
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: '#475569' }}
                width={120}
              />
              <Tooltip />
              <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={22}>
                {funnelData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white border rounded-lg shadow p-5">
          <div className="mb-4">
            <h3 className="text-lg font-bold text-gray-900">Seat Fill Overview</h3>
            <p className="text-sm text-gray-500">Filled vs available seats per branch</p>
          </div>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={seatFillData} margin={{ top: 8, right: 12, left: 8, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="branch" angle={-25} textAnchor="end" interval={0} height={60} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="filled" stackId="seats" fill="#2563EB" name="Filled" />
              <Bar dataKey="available" stackId="seats" fill="#10B981" name="Available" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function AdmissionTrendChart({ period, onPeriodChange, data, loading }) {
  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <h3 className="text-lg font-bold text-gray-900">Application Trend</h3>
        <div className="inline-flex bg-gray-100 rounded-lg p-1">
          {PERIODS.map((p) => (
            <button
              key={p}
              type="button"
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                period === p ? 'bg-white shadow text-gray-900' : 'text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => onPeriodChange(p)}
            >
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="submitted" stroke="#3B82F6" strokeWidth={2} />
          <Line type="monotone" dataKey="admitted" stroke="#059669" strokeWidth={2} />
          <Line type="monotone" dataKey="rejected" stroke="#EF4444" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
      {loading ? <p className="text-xs text-gray-500 mt-2">Refreshing trend data...</p> : null}
    </div>
  );
}

function MetricCard({ title, value, subtitle, icon: Icon, loading }) {
  return (
    <div className="bg-white border rounded-lg shadow p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{loading ? '--' : value}</p>
          <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
        </div>
        <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}

function mergeTrendData(trend, period) {
  if (!trend) return [];

  const buckets = new Map();
  const ingest = (series, key) => {
    (series || []).forEach((point) => {
      const date = point.date;
      if (!buckets.has(date)) {
        buckets.set(date, {
          date,
          label: formatTrendLabel(date, period),
          submitted: 0,
          admitted: 0,
          rejected: 0,
        });
      }
      buckets.get(date)[key] = toNumber(point.count);
    });
  };

  ingest(trend.submitted, 'submitted');
  ingest(trend.admitted, 'admitted');
  ingest(trend.rejected, 'rejected');

  return Array.from(buckets.values()).sort((a, b) => a.date.localeCompare(b.date));
}

function formatTrendLabel(date, period) {
  const dt = new Date(date);
  if (Number.isNaN(dt.getTime())) return date;
  if (period === 'monthly') {
    return dt.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' });
  }
  if (period === 'weekly') {
    return dt.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
  }
  return dt.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
}

function buildFunnelData(statusBreakdown) {
  const source = statusBreakdown || {};
  return [
    { name: 'Draft', count: toNumber(source.draft), color: '#94A3B8' },
    { name: 'Submitted', count: toNumber(source.submitted), color: '#3B82F6' },
    { name: 'In Review', count: toNumber(source.under_verification), color: '#F59E0B' },
    { name: 'Verified', count: toNumber(source.verified), color: '#22C55E' },
    { name: 'Allocated', count: toNumber(source.seat_allocated), color: '#8B5CF6' },
    { name: 'Fee Pending', count: toNumber(source.fee_pending), color: '#EC4899' },
    { name: 'Admitted', count: toNumber(source.admitted), color: '#059669' },
    { name: 'Rejected', count: toNumber(source.rejected), color: '#EF4444' },
  ];
}

function buildSeatFillData(byBranch) {
  return (byBranch || []).map((item) => ({
    branch: item.branch_code || item.branch_name,
    filled: toNumber(item.allocated_seats),
    available: toNumber(item.available_seats),
  }));
}

function toNumber(value) {
  const num = Number(value ?? 0);
  return Number.isFinite(num) ? num : 0;
}

function formatINR(value) {
  const amount = toNumber(value);
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}
