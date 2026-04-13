import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { 
  Users, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Loader
} from 'lucide-react';
import api from '../../services/api';
import './BulkAllocatePage.css';

const QUOTA_LABELS = {
  general: 'General',
  obc: 'OBC',
  sc: 'SC',
  st: 'ST',
  management: 'Management',
  nri: 'NRI',
};

export const BulkAllocatePage = () => {
  const [selectedBranch, setSelectedBranch] = useState('');
  const [selectedQuota, setSelectedQuota] = useState('');
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [showResults, setShowResults] = useState(false);
  const [results, setResults] = useState(null);

  const { data: availability } = useQuery({
    queryKey: ['seat-availability'],
    queryFn: () => api.get('/seats/availability/').then(res => res.data),
    enabled: true,
  });

  const { data: suggestions, isLoading: loadingSuggestions, refetch: refetchSuggestions } = useQuery({
    queryKey: ['allocation-suggest', selectedBranch, selectedQuota],
    queryFn: () => api.get('/officer/seats/allocation/suggest/', {
      params: {
        branch_id: selectedBranch,
        quota: selectedQuota,
        limit: 50,
      },
    }).then(res => res.data),
    enabled: !!selectedBranch && !!selectedQuota,
    staleTime: 0,
  });

  const bulkMutation = useMutation({
    mutationFn: () => {
      const items = Array.from(selectedIds).map(appId => ({
        application_id: appId,
        branch_id: selectedBranch,
        quota: selectedQuota,
      }));
      return api.post('/officer/seats/allocate/bulk/', { items });
    },
    onSuccess: (res) => {
      setResults(res.data);
      setShowResults(true);
      refetchSuggestions();
    },
  });

  const autoAllocateMutation = useMutation({
    mutationFn: (count) => api.post('/officer/seats/allocation/auto-allocate/', {
      branch_id: selectedBranch,
      quota: selectedQuota,
      count,
    }),
    onSuccess: (res) => {
      setResults(res.data);
      setShowResults(true);
      refetchSuggestions();
    },
  });

  const toggleSelection = (appId) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(appId)) {
        next.delete(appId);
      } else {
        next.add(appId);
      }
      return next;
    });
  };

  const selectTopN = (n) => {
    const topIds = suggestions?.candidates?.slice(0, n).map(c => c.application_id) || [];
    setSelectedIds(new Set(topIds));
  };

  const clearSelection = () => {
    setSelectedIds(new Set());
  };

  const handleBulkAllocate = () => {
    bulkMutation.mutate();
  };

  const handleAutoAllocate = (count) => {
    autoAllocateMutation.mutate(count);
  };

  const getBranchAvailability = (branchId, quota) => {
    const branch = availability?.find(b => b.branch_id === branchId);
    const q = branch?.quotas?.find(q => q.quota === quota);
    return q?.available || 0;
  };

  const branches = availability || [];
  const quotas = Object.entries(QUOTA_LABELS);
  const currentAvailability = selectedBranch && selectedQuota ? getBranchAvailability(selectedBranch, selectedQuota) : 0;

  return (
    <div className="bulk-allocate-page">
      <div className="page-header">
        <h1>Bulk Allocate</h1>
        <p>Allocate seats to multiple candidates at once</p>
      </div>

      <div className="filters-card">
        <div className="filters-row">
          <div className="filter-group">
            <label>Branch</label>
            <select 
              value={selectedBranch} 
              onChange={(e) => { setSelectedBranch(e.target.value); setSelectedIds(new Set()); setShowResults(false); }}
            >
              <option value="">Select Branch</option>
              {branches.map(b => (
                <option key={b.branch_id} value={b.branch_id}>
                  {b.branch_code} - {b.branch_name}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Quota</label>
            <select 
              value={selectedQuota} 
              onChange={(e) => { setSelectedQuota(e.target.value); setSelectedIds(new Set()); setShowResults(false); }}
            >
              <option value="">Select Quota</option>
              {quotas.map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>

          <div className="availability-display">
            <span className="label">Available Seats</span>
            <span className="value">{currentAvailability}</span>
          </div>
        </div>
      </div>

      {selectedBranch && selectedQuota && (
        <>
          <div className="actions-bar">
            <div className="selection-info">
              <span>{selectedIds.size} selected</span>
              {suggestions?.candidates && (
                <span className="total">of {suggestions.candidates.length} candidates</span>
              )}
            </div>

            <div className="quick-actions">
              {currentAvailability > 0 && (
                <>
                  <button 
                    className="btn-quick"
                    onClick={() => selectTopN(Math.min(5, currentAvailability))}
                    disabled={loadingSuggestions}
                  >
                    Top 5
                  </button>
                  <button 
                    className="btn-quick"
                    onClick={() => selectTopN(Math.min(10, currentAvailability))}
                    disabled={loadingSuggestions}
                  >
                    Top 10
                  </button>
                  <button 
                    className="btn-quick"
                    onClick={() => selectTopN(currentAvailability)}
                    disabled={loadingSuggestions}
                  >
                    Fill All ({currentAvailability})
                  </button>
                </>
              )}
              <button 
                className="btn-clear"
                onClick={clearSelection}
                disabled={selectedIds.size === 0}
              >
                Clear
              </button>
            </div>
          </div>

          <div className="candidates-card">
            <div className="candidates-header">
              <h3>Merit-Ranked Candidates</h3>
            </div>

            {loadingSuggestions ? (
              <div className="loading-state">
                <Loader className="spinner-icon" />
                <span>Loading candidates...</span>
              </div>
            ) : suggestions?.candidates?.length === 0 ? (
              <div className="empty-state">
                <Users size={32} />
                <p>No eligible candidates found</p>
              </div>
            ) : (
              <div className="candidates-list">
                <div className="list-header">
                  <span className="col-check"></span>
                  <span className="col-rank">Rank</span>
                  <span className="col-app">Application</span>
                  <span className="col-name">Student</span>
                  <span className="col-score">Merit Score</span>
                  <span className="col-category">Category</span>
                  <span className="col-pref">Preference #</span>
                </div>
                {suggestions?.candidates?.map((candidate, idx) => {
                  const isSelected = selectedIds.has(candidate.application_id);
                  const isAllocated = candidate.merit_score === 0;
                  return (
                    <div 
                      key={candidate.application_id} 
                      className={`candidate-row ${isSelected ? 'selected' : ''} ${isAllocated ? 'allocated' : ''}`}
                    >
                      <span className="col-check">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelection(candidate.application_id)}
                          disabled={isAllocated}
                        />
                      </span>
                      <span className="col-rank">#{idx + 1}</span>
                      <span className="col-app">{candidate.application_number}</span>
                      <span className="col-name">{candidate.student_name}</span>
                      <span className="col-score">{candidate.merit_score}</span>
                      <span className="col-category">{candidate.category}</span>
                      <span className="col-pref">{candidate.branch_preference_order || '-'}</span>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="candidates-footer">
              <button 
                className="btn-allocate"
                onClick={handleBulkAllocate}
                disabled={selectedIds.size === 0 || bulkMutation.isPending}
              >
                {bulkMutation.isPending ? (
                  <>
                    <Loader className="btn-spinner" />
                    Allocating...
                  </>
                ) : (
                  <>
                    <Users size={18} />
                    Allocate Selected ({selectedIds.size})
                  </>
                )}
              </button>

              {currentAvailability > 0 && suggestions?.candidates?.length > 0 && (
                <button 
                  className="btn-auto"
                  onClick={() => handleAutoAllocate(currentAvailability)}
                  disabled={autoAllocateMutation.isPending}
                >
                  {autoAllocateMutation.isPending ? (
                    <>
                      <Loader className="btn-spinner" />
                      Auto-allocating...
                    </>
                  ) : (
                    `Auto-Fill ${currentAvailability} Seats by Merit`
                  )}
                </button>
              )}
            </div>
          </div>
        </>
      )}

      {showResults && results && (
        <div className="results-card">
          <div className="results-header">
            <h3>Allocation Results</h3>
            <button className="btn-close" onClick={() => setShowResults(false)}>
              <XCircle size={18} />
            </button>
          </div>

          <div className="results-summary">
            <div className="summary-item success">
              <CheckCircle size={20} />
              <span className="count">{results.succeeded}</span>
              <span className="label">Successful</span>
            </div>
            <div className="summary-item failure">
              <AlertCircle size={20} />
              <span className="count">{results.failed}</span>
              <span className="label">Failed</span>
            </div>
          </div>

          {results.results?.some(r => !r.success) && (
            <div className="failures-list">
              <h4>Failures</h4>
              {results.results?.filter(r => !r.success).map((r, idx) => (
                <div key={idx} className="failure-item">
                  <XCircle size={14} />
                  <span>{r.application_number}</span>
                  <span className="reason">{r.error}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BulkAllocatePage;