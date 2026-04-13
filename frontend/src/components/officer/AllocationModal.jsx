import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  X, 
  CheckCircle, 
  AlertCircle, 
  Users,
  Award,
  ChevronRight
} from 'lucide-react';
import api from '../../services/api';
import './AllocationModal.css';

const QUOTA_LABELS = {
  general: 'General',
  obc: 'OBC',
  sc: 'SC',
  st: 'ST',
  management: 'Management',
  nri: 'NRI',
};

const AllocationModal = ({ application, onClose }) => {
  const queryClient = useQueryClient();
  const [selectedBranch, setSelectedBranch] = useState(null);
  const [selectedQuota, setSelectedQuota] = useState(null);
  const [step, setStep] = useState('select');

  const { data: availability, isLoading: loadingAvailability } = useQuery({
    queryKey: ['seat-availability'],
    queryFn: () => api.get('/seats/availability/').then(res => res.data),
    enabled: !!application,
  });

  const allocateMutation = useMutation({
    mutationFn: ({ branchId, quota }) => api.post(`/officer/seats/allocate/${application.id}/`, {
      branch_id: branchId,
      quota,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['officer-application', application.id] });
      queryClient.invalidateQueries({ queryKey: ['officer-applications'] });
      queryClient.invalidateQueries({ queryKey: ['seat-availability'] });
      setStep('success');
    },
    onError: (err) => {
      const errorCode = err.response?.data?.code;
      const errorMessage = err.response?.data?.error;
      
      if (errorCode === 'NO_SEATS' || errorMessage?.includes('No seats available')) {
        setStep('no-seats');
        queryClient.invalidateQueries({ queryKey: ['seat-availability'] });
      } else if (errorCode === 'ALREADY_ALLOCATED') {
        setStep('already-allocated');
      } else {
        setStep('error');
      }
    },
  });

  const branchPreferences = application?.branch_preferences || [];
  
  const getBranchInfo = (branchId) => {
    return availability?.find(b => b.branch_id === branchId);
  };

  const getAvailableForBranch = (branchId, quota) => {
    const branch = getBranchInfo(branchId);
    if (!branch) return 0;
    const q = branch.quotas?.find(q => q.quota === quota);
    return q?.available || 0;
  };

  const handleAllocate = () => {
    if (selectedBranch && selectedQuota) {
      setStep('confirm');
    }
  };

  const confirmAllocate = () => {
    allocateMutation.mutate({ branchId: selectedBranch, quota: selectedQuota });
  };

  if (!application) return null;

  return (
    <div className="allocation-modal-overlay" onClick={onClose}>
      <div className="allocation-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Allocate Seat</h3>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-subheader">
          <span className="app-number">{application.application_number}</span>
          <span className="student-name">{application.student_profile?.full_name}</span>
        </div>

        {step === 'select' && (
          <>
            <div className="allocation-section">
              <h4>Branch Preferences</h4>
              <div className="preference-list">
                {branchPreferences.map((branchId, index) => {
                  const branchData = getBranchInfo(branchId);
                  if (!branchData) return null;
                  
                  return (
                    <div key={branchId} className="preference-item">
                      <div className="preference-header">
                        <span className="pref-rank">#{index + 1}</span>
                        <span className="pref-branch">{branchData.branch_name}</span>
                        <span className="pref-code">{branchData.branch_code}</span>
                      </div>
                      <div className="quota-options">
                        {branchData.quotas?.map(q => {
                          const isAvailable = q.available > 0;
                          const isSelected = selectedBranch === branchId && selectedQuota === q.quota;
                          return (
                            <button
                              key={q.quota}
                              className={`quota-btn ${isSelected ? 'selected' : ''} ${!isAvailable ? 'disabled' : ''}`}
                              onClick={() => isAvailable && setSelectedBranch(branchId) && setSelectedQuota(q.quota)}
                              disabled={!isAvailable}
                            >
                              <span className="quota-label">{QUOTA_LABELS[q.quota]}</span>
                              <span className="quota-avail">{q.available} seats</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="modal-actions">
              <button className="btn-secondary" onClick={onClose}>Cancel</button>
              <button 
                className="btn-primary"
                onClick={handleAllocate}
                disabled={!selectedBranch || !selectedQuota}
              >
                Continue
              </button>
            </div>
          </>
        )}

        {step === 'confirm' && (
          <div className="confirm-step">
            <div className="confirm-details">
              <div className="confirm-item">
                <Users size={18} />
                <span>{application.student_profile?.full_name}</span>
              </div>
              <ChevronRight size={16} className="arrow" />
              <div className="confirm-item">
                <Award size={18} />
                <span>{getBranchInfo(selectedBranch)?.branch_name}</span>
              </div>
              <div className="confirm-quota">
                {QUOTA_LABELS[selectedQuota]} Quota
              </div>
            </div>
            <div className="availability-summary">
              <span>Available: {getAvailableForBranch(selectedBranch, selectedQuota)} seats</span>
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setStep('select')}>Back</button>
              <button 
                className="btn-primary"
                onClick={confirmAllocate}
                disabled={allocateMutation.isPending}
              >
                {allocateMutation.isPending ? 'Allocating...' : 'Allocate'}
              </button>
            </div>
          </div>
        )}

        {step === 'success' && (
          <div className="success-step">
            <CheckCircle size={48} className="success-icon" />
            <h4>Seat Allocated Successfully</h4>
            <p>
              {application.student_profile?.full_name} has been allocated to{' '}
              {getBranchInfo(selectedBranch)?.branch_name} under {QUOTA_LABELS[selectedQuota]} quota.
            </p>
            <button className="btn-primary" onClick={onClose}>Done</button>
          </div>
        )}

        {step === 'no-seats' && (
          <div className="error-step no-seats">
            <AlertCircle size={48} className="error-icon" />
            <h4>Seat No Longer Available</h4>
            <p>The seat was allocated to another student while you were on this page. Availability has been updated.</p>
            <div className="refresh-info">
              <span>Current availability: {getAvailableForBranch(selectedBranch, selectedQuota)} seats</span>
            </div>
            <button className="btn-secondary" onClick={() => { queryClient.invalidateQueries({ queryKey: ['seat-availability'] }); setStep('select'); }}>
              View Updated Availability
            </button>
          </div>
        )}

        {step === 'already-allocated' && (
          <div className="error-step">
            <AlertCircle size={48} className="error-icon" />
            <h4>Already Allocated</h4>
            <p>This application already has a seat allocated. Please refresh to see the current allocation.</p>
            <button className="btn-secondary" onClick={onClose}>Close</button>
          </div>
        )}

        {step === 'error' && (
          <div className="error-step">
            <AlertCircle size={48} className="error-icon" />
            <h4>Allocation Failed</h4>
            <p>{allocateMutation.error?.response?.data?.error || 'Please try again.'}</p>
            <button className="btn-secondary" onClick={() => setStep('select')}>Try Again</button>
          </div>
        )}
      </div>
    </div>
  );
};

export const DeallocateModal = ({ application, onClose }) => {
  const queryClient = useQueryClient();
  const [reason, setReason] = useState('');
  const [step, setStep] = useState('form');

  const deallocateMutation = useMutation({
    mutationFn: (reason) => api.post(`/officer/seats/deallocate/${application.id}/`, { reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['officer-application', application.id] });
      queryClient.invalidateQueries({ queryKey: ['officer-applications'] });
      setStep('success');
    },
    onError: () => {
      setStep('error');
    },
  });

  const handleDeallocate = () => {
    if (reason.length >= 10) {
      deallocateMutation.mutate(reason);
    }
  };

  if (!application) return null;

  return (
    <div className="allocation-modal-overlay" onClick={onClose}>
      <div className="allocation-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Deallocate Seat</h3>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-subheader">
          <span className="app-number">{application.application_number}</span>
          <span className="student-name">{application.student_profile?.full_name}</span>
        </div>

        {step === 'form' && (
          <>
            <div className="current-allocation">
              <span>Currently allocated to:</span>
              <strong>{application.allocated_branch} ({application.allocated_quota})</strong>
            </div>

            <div className="reason-input">
              <label>Reason for deallocation (minimum 10 characters)</label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Enter reason..."
                rows={3}
              />
              <span className="char-count">{reason.length} / 10 min</span>
            </div>

            <div className="modal-actions">
              <button className="btn-secondary" onClick={onClose}>Cancel</button>
              <button 
                className="btn-danger"
                onClick={handleDeallocate}
                disabled={reason.length < 10 || deallocateMutation.isPending}
              >
                {deallocateMutation.isPending ? 'Deallocating...' : 'Deallocate'}
              </button>
            </div>
          </>
        )}

        {step === 'success' && (
          <div className="success-step">
            <CheckCircle size={48} className="success-icon" />
            <h4>Seat Deallocated</h4>
            <p>The seat has been removed from this application.</p>
            <button className="btn-primary" onClick={onClose}>Done</button>
          </div>
        )}

        {step === 'error' && (
          <div className="error-step">
            <AlertCircle size={48} className="error-icon" />
            <h4>Deallocation Failed</h4>
            <p>{deallocateMutation.error?.response?.data?.error || 'Please try again.'}</p>
            <button className="btn-secondary" onClick={() => setStep('form')}>Try Again</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AllocationModal;