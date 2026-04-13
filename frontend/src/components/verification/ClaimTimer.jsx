import React, { useState, useEffect, useCallback } from 'react';
import { Clock, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import './ClaimTimer.css';

export const ClaimTimer = ({ claimExpiresAt, onExtend, isExtending }) => {
  const navigate = useNavigate();
  const [timeLeft, setTimeLeft] = useState(null);
  const [isExpired, setIsExpired] = useState(false);
  const [showExpiredModal, setShowExpiredModal] = useState(false);

  const calculateTimeLeft = useCallback(() => {
    if (!claimExpiresAt) return null;
    
    const expiryDate = new Date(claimExpiresAt);
    const now = new Date();
    const diff = expiryDate - now;

    if (diff <= 0) {
      return { expired: true, total: 0 };
    }

    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);

    return { 
      expired: false, 
      total: diff,
      minutes, 
      seconds 
    };
  }, [claimExpiresAt]);

  useEffect(() => {
    const updateTimer = () => {
      const time = calculateTimeLeft();
      
      if (time?.expired) {
        setIsExpired(true);
        setShowExpiredModal(true);
        setTimeLeft(null);
      } else if (time) {
        setTimeLeft(time);
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [calculateTimeLeft]);

  const getTimerClass = () => {
    if (!timeLeft) return '';
    if (timeLeft.total < 5 * 60000) return 'critical';
    if (timeLeft.total < 10 * 60000) return 'warning';
    return 'normal';
  };

  const formatTime = () => {
    if (!timeLeft) return '';
    const { minutes, seconds } = timeLeft;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const handleExtendClaim = async () => {
    try {
      await onExtend?.();
      toast.success('Claim extended by 30 minutes');
    } catch (error) {
      toast.error('Failed to extend claim');
    }
  };

  const handleCloseModal = () => {
    setShowExpiredModal(false);
    navigate('/verification/queue');
  };

  if (!claimExpiresAt || isExpired) {
    return null;
  }

  return (
    <>
      <div className={`claim-timer ${getTimerClass()}`}>
        <Clock size={16} className="timer-icon" />
        <span className="timer-text">
          {formatTime()} remaining
        </span>
        {timeLeft && timeLeft.total < 10 * 60000 && (
          <button 
            className="extend-btn"
            onClick={handleExtendClaim}
            disabled={isExtending}
            title="Extend claim by 30 minutes"
          >
            +30s
          </button>
        )}
      </div>

      {showExpiredModal && (
        <div className="modal-overlay">
          <div className="modal-content expired-modal">
            <div className="modal-header">
              <AlertTriangle size={32} className="expired-icon" />
              <h2>Claim Expired</h2>
            </div>
            <p>Your claim has expired. The application has been returned to the queue.</p>
            <button className="btn-redirect" onClick={handleCloseModal}>
              Return to Queue
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default ClaimTimer;
