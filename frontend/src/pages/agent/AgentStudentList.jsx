import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { agentApi } from '../../services/agentApi';
import { PageHeader } from '../../components/layout/PageHeader';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Input } from '../../components/ui/Input';
import { Search, Filter, Loader2, Eye, UserPlus } from 'lucide-react';
import { Link } from 'react-router-dom';

export function AgentStudentList() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');

  const { data, isLoading, isPlaceholderData } = useQuery({
    queryKey: ['agent-students', page, search, status],
    queryFn: () => agentApi.getStudents({ page, search, status }).then(r => r.data),
    placeholderData: (previous) => previous,
  });

  const handleSearchChange = (e) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const handleStatusChange = (e) => {
    setStatus(e.target.value);
    setPage(1);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <PageHeader 
          title="My Students" 
          subtitle="Track and manage student applications referred by you" 
        />
        <Link 
          to="/agent/students/register" 
          className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg font-bold hover:bg-blue-700 transition"
        >
          <UserPlus size={18} />
          Register Student
        </Link>
      </div>

      <Card className="p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input 
              placeholder="Search by name, email or application #..." 
              className="pl-10"
              value={search}
              onChange={handleSearchChange}
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-gray-400" />
            <select 
              className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2"
              value={status}
              onChange={handleStatusChange}
            >
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="submitted">Submitted</option>
              <option value="under_verification">Under Verification</option>
              <option value="verified">Verified</option>
              <option value="seat_allocated">Seat Allocated</option>
              <option value="fee_pending">Fee Pending</option>
              <option value="admitted">Admitted</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>
      </Card>

      <Card className="overflow-hidden border shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-gray-500">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-4">Student Name</th>
                <th className="px-6 py-4">Application #</th>
                <th className="px-6 py-4">Current Status</th>
                <th className="px-6 py-4">Branch</th>
                <th className="px-6 py-4">Submitted Date</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {isLoading && !isPlaceholderData ? (
                <tr>
                  <td colSpan="6" className="px-6 py-12">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
                      <p className="text-gray-400 font-medium font-inter">Loading student data...</p>
                    </div>
                  </td>
                </tr>
              ) : data?.results?.length > 0 ? (
                data.results.map((student) => (
                  <tr key={student.id} className="bg-white hover:bg-gray-50 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="font-bold text-gray-900">{student.full_name}</div>
                      <div className="text-xs text-gray-400 mt-0.5">{student.email}</div>
                    </td>
                    <td className="px-6 py-4 font-mono font-medium text-gray-600">
                      {student.application_number || '—'}
                    </td>
                    <td className="px-6 py-4">
                      <Badge variant={getStatusVariant(student.status)}>
                        {student.status?.replace('_', ' ') || 'Draft'}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 font-medium text-gray-700">
                      {student.branch_name || 'Not Allocated'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {student.submitted_at 
                        ? new Date(student.submitted_at).toLocaleDateString('en-IN', {
                            day: '2-digit', month: 'short', year: 'numeric'
                          })
                        : '—'
                      }
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link 
                        to={`/agent/students/${student.id}`}
                        className="p-2 text-gray-400 hover:text-blue-600 inline-block"
                        title="View Application"
                      >
                        <Eye size={18} />
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="px-6 py-12 text-center text-gray-400 italic">
                    No students found matching your criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data?.count > 0 && (
          <div className="px-6 py-4 bg-gray-50 border-t flex items-center justify-between">
            <span className="text-sm text-gray-700">
              Showing <span className="font-bold">{(page-1)*20 + 1}</span> to <span className="font-bold">{Math.min(page*20, data.count)}</span> of <span className="font-bold">{data.count}</span> results
            </span>
            <div className="flex gap-2">
              <button
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                className="px-3 py-1 bg-white border rounded text-sm font-medium disabled:opacity-50 hover:bg-gray-50"
              >
                Previous
              </button>
              <button
                disabled={page * 20 >= data.count}
                onClick={() => setPage(p => p + 1)}
                className="px-3 py-1 bg-white border rounded text-sm font-medium disabled:opacity-50 hover:bg-gray-50"
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

function getStatusVariant(status) {
  const map = {
    'draft': 'neutral',
    'submitted': 'primary',
    'under_verification': 'warning',
    'verified': 'success',
    'seat_allocated': 'purple',
    'fee_pending': 'orange',
    'admitted': 'success',
    'rejected': 'danger',
  };
  return map[status] || 'neutral';
}
