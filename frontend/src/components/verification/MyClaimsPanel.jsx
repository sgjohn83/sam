import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  ChevronDown, 
  ChevronUp, 
  Clock, 
  Play, 
  RotateCcw, 
  AlertTriangle 
} from 'lucide-react';
import toast from 'react-hot-toast';
import { verificationApi } from '../../services/verificationApi';
import './MyClaimsPanel.css';

const ClaimItem = ({ claim, onRelease }) => {
  const navigate = useNavigate();
  const [timeLeft, setTimeLeft] = useState('');
  const [isWarning, setIsWarning] = useState(false);

  useEffect(() => {
    const calculateTime = () => {
      const claimDate = new Date(claim.claimed_at);
      const expiryDate = new Date(claimDate.getTime() + 30 * 60000); // 30 mins
      const now = new Date();
      const diff = expiryDate - now;

      if (diff <= 0) {
        if (timeLeft && timeLeft !== 'Expired') {
          toast.error(`Your review of ${claim.application_number} was auto-released due to inactivity`, {
            duration: 6000,
            icon: '⏰'
          });
          queryClient.invalidateQueries({ queryKey: ['my-claims'] });
          queryClient.invalidateQueries({ queryKey: ['verification-queue'] });
        }
        setTimeLeft('Expired');
        setIsWarning(true);
        return;
      }

      const minutes = Math.floor(diff / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);
      
      setIsWarning(minutes < 5);
      setTimeLeft(`${minutes}:${seconds.toString().padStart(2, '0')} left`);
    };

    calculateTime();
    const interval = setInterval(calculateTime, 1000);
    return () => clearInterval(interval);
  }, [claim.claimed_at]);

  return (
    <div className="claim-item">
      <div className="claim-item-details">
        <div className="claim-identity">
          <span className="claim-app-no">{claim.application_number}</span>
          <span className="claim-student">{claim.student_name}</span>
        </div>
        <div className="claim-meta">
          <div className={`claim-conf ${claim.confidence_badge.level}`}>
            {Math.round(claim.overall_confidence * 100)}%
          </div>
          <div className={`claim-timer ${isWarning ? 'warning' : ''}`}>
            <Clock size={14} />
            <span>{timeLeft}</span>
          </div>
        </div>
      </div>
      <div className="claim-actions">
        <button 
          className="continue-btn"
          onClick={() => navigate(`/verification/review/${claim.application_id}`)}
        >
          <Play size={14} />
          Continue Review
        </button>
        <button 
          className="release-btn"
          onClick={() => onRelease(claim.application_id)}
        >
          <RotateCcw size={14} />
          Release
        </button>
      </div>
    </div>
  );
};

export const MyClaimsPanel = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const queryClient = useQueryClient();

  const { data: claims, isLoading } = useQuery({
    queryKey: ['my-claims'],
    queryFn: () => verificationApi.getMyClaims().then(res => res.data),
    refetchInterval: 30000, // Sync every 30s
  });

  const releaseMutation = useMutation({
    mutationFn: (id) => verificationApi.releaseApplication(id),
    onSuccess: () => {
      toast.success('Application released back to queue');
      queryClient.invalidateQueries({ queryKey: ['my-claims'] });
      queryClient.invalidateQueries({ queryKey: ['verification-queue'] });
      queryClient.invalidateQueries({ queryKey: ['verification-stats'] });
    },
    onError: () => {
      toast.error('Failed to release application');
    }
  });

  if (isLoading || !claims || claims.length === 0) return null;

  return (
    <div className={`my-claims-panel ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="panel-header" onClick={() => setIsCollapsed(!isCollapsed)}>
        <div className="header-title">
          <UserCheck size={20} className="header-icon" />
          <span>My Active Reviews ({claims.length})</span>
        </div>
        <button className="collapse-toggle">
          {isCollapsed ? <ChevronDown size={20} /> : <ChevronUp size={20} />}
        </button>
      </div>

      {!isCollapsed && (
        <div className="panel-content">
          {claims.map(claim => (
            <ClaimItem 
              key={claim.application_id} 
              claim={claim} 
              onRelease={(id) => releaseMutation.mutate(id)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Internal icon helper to avoid extra imports if possible or reuse existing ones
const UserCheck = ({ size, className }) => (
  <svg 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/>
  </svg>
);
