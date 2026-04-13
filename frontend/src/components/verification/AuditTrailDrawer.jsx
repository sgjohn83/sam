import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  X, 
  Clock, 
  User, 
  FileText, 
  Lock, 
  Unlock,
  Edit3,
  CheckCircle,
  AlertCircle,
  ChevronRight,
  ChevronDown
} from 'lucide-react';
import { verificationApi } from '../../services/verificationApi';
import './AuditTrailDrawer.css';

const getActionIcon = (action) => {
  switch (action) {
    case 'lock':
      return <Lock size={14} />;
    case 'unlock':
      return <Unlock size={14} />;
    case 'field_edit':
      return <Edit3 size={14} />;
    case 'field_approve':
      return <CheckCircle size={14} />;
    case 'document_verify':
      return <CheckCircle size={14} />;
    case 'reject_doc':
      return <AlertCircle size={14} />;
    case 'claim':
      return <User size={14} />;
    case 'release':
      return <User size={14} />;
    default:
      return <FileText size={14} />;
  }
};

const getActionColor = (action) => {
  switch (action) {
    case 'lock':
      return 'purple';
    case 'unlock':
      return 'orange';
    case 'field_edit':
      return 'blue';
    case 'field_approve':
      return 'green';
    case 'document_verify':
      return 'green';
    case 'reject_doc':
      return 'red';
    case 'claim':
      return 'blue';
    case 'release':
      return 'gray';
    default:
      return 'gray';
  }
};

const formatAction = (action) => {
  return action.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
};

const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

const DiffViewer = ({ before, after }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!before && !after) return null;
  
  const beforeKeys = before ? Object.keys(before) : [];
  const afterKeys = after ? Object.keys(after) : [];
  const allKeys = [...new Set([...beforeKeys, ...afterKeys])];
  
  return (
    <div className="diff-viewer">
      <button 
        className="diff-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        <span>View changes</span>
      </button>
      
      {isExpanded && (
        <div className="diff-content">
          {allKeys.map(key => {
            const beforeVal = before?.[key];
            const afterVal = after?.[key];
            const hasChange = beforeVal !== afterVal;
            
            if (!hasChange) return null;
            
            return (
              <div key={key} className="diff-row">
                <span className="diff-field">{key}:</span>
                {beforeVal !== undefined && (
                  <span className="diff-old">{String(beforeVal)}</span>
                )}
                {beforeVal !== undefined && afterVal !== undefined && (
                  <span className="diff-arrow">→</span>
                )}
                {afterVal !== undefined && (
                  <span className="diff-new">{String(afterVal)}</span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

const AuditEvent = ({ event, isLast }) => {
  const color = getActionColor(event.action);
  
  return (
    <div className="audit-event">
      <div className="event-connector">
        <div className={`event-dot ${color}`}>
          {getActionIcon(event.action)}
        </div>
        {!isLast && <div className="event-line" />}
      </div>
      
      <div className="event-content">
        <div className="event-header">
          <span className={`event-label ${color}`}>{formatAction(event.action)}</span>
          <span className="event-timestamp">
            <Clock size={12} />
            {formatTimestamp(event.created_at)}
          </span>
        </div>
        
        <div className="event-actor">
          <User size={12} />
          <span>{event.actor?.email || 'System'}</span>
        </div>
        
        {event.ip_address && (
          <div className="event-ip">IP: {event.ip_address}</div>
        )}
        
        <DiffViewer before={event.before_json} after={event.after_json} />
      </div>
    </div>
  );
};

export const AuditTrailDrawer = ({ applicationId, isOpen, onClose }) => {
  const { data: auditLogs, isLoading, error } = useQuery({
    queryKey: ['audit-logs', applicationId],
    queryFn: () => verificationApi.getAuditLogs(applicationId).then(res => res.data),
    enabled: isOpen && !!applicationId,
  });

  if (!isOpen) return null;

  return (
    <div className="audit-drawer-overlay" onClick={onClose}>
      <div className="audit-drawer" onClick={e => e.stopPropagation()}>
        <div className="audit-drawer-header">
          <h3>Audit Trail</h3>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        
        <div className="audit-drawer-content">
          {isLoading ? (
            <div className="audit-loading">Loading audit logs...</div>
          ) : error ? (
            <div className="audit-error">Failed to load audit logs</div>
          ) : auditLogs && auditLogs.length > 0 ? (
            <div className="audit-events">
              {auditLogs.map((event, index) => (
                <AuditEvent 
                  key={event.id || index} 
                  event={event}
                  isLast={index === auditLogs.length - 1}
                />
              ))}
            </div>
          ) : (
            <div className="audit-empty">No audit logs available</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuditTrailDrawer;