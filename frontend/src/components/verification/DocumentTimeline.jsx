import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  ChevronDown, 
  ChevronRight, 
  Upload, 
  FileText, 
  XCircle, 
  CheckCircle, 
  AlertTriangle,
  Clock
} from 'lucide-react';
import { verificationApi } from '../../services/verificationApi';
import './DocumentTimeline.css';

const getEventIcon = (eventType) => {
  switch (eventType) {
    case 'upload':
      return <Upload size={14} />;
    case 'rejection':
      return <XCircle size={14} />;
    case 'ocr_complete':
      return <FileText size={14} />;
    default:
      return <Clock size={14} />;
  }
};

const getEventColor = (eventType) => {
  switch (eventType) {
    case 'upload':
      return 'blue';
    case 'rejection':
      return 'red';
    case 'ocr_complete':
      return 'green';
    default:
      return 'gray';
  }
};

const formatEventLabel = (eventType) => {
  switch (eventType) {
    case 'upload':
      return 'Document Uploaded';
    case 'rejection':
      return 'Document Rejected';
    case 'ocr_complete':
      return 'OCR Complete';
    default:
      return eventType;
  }
};

const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const EventDetails = ({ event }) => {
  const { event_type, details, version } = event;
  
  if (event_type === 'upload') {
    return (
      <div className="event-details">
        <span className="detail-label">Version:</span> {version}
        <span className="detail-divider">•</span>
        <span className="detail-label">File:</span> {details.file_name}
      </div>
    );
  }
  
  if (event_type === 'rejection') {
    return (
      <div className="event-details">
        <span className="detail-label">Reason:</span> {details.reason}
        {details.category && (
          <>
            <span className="detail-divider">•</span>
            <span className="detail-label">Category:</span> {details.category}
          </>
        )}
      </div>
    );
  }
  
  if (event_type === 'ocr_complete') {
    const confidence = Math.round((details.overall_confidence || 0) * 100);
    const confidenceColor = confidence >= 90 ? 'green' : confidence >= 70 ? 'yellow' : 'red';
    return (
      <div className="event-details">
        <span className="detail-label">Confidence:</span> 
        <span className={`confidence-badge ${confidenceColor}`}>{confidence}%</span>
        <span className="detail-divider">•</span>
        <span className="detail-label">Fields:</span> {details.field_count}
      </div>
    );
  }
  
  return null;
};

export const DocumentTimeline = ({ documentId, uploadVersion }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const { data: history, isLoading, error } = useQuery({
    queryKey: ['document-reupload-history', documentId],
    queryFn: () => verificationApi.getReuploadHistory(documentId).then(res => res.data),
    enabled: isExpanded && !!documentId,
  });

  if (uploadVersion <= 1) {
    return null;
  }

  return (
    <div className="document-timeline">
      <button 
        className="timeline-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        <Clock size={14} />
        <span className="timeline-label">Upload History</span>
        <span className="timeline-version-badge">v{uploadVersion}</span>
      </button>

      {isExpanded && (
        <div className="timeline-content">
          {isLoading ? (
            <div className="timeline-loading">Loading history...</div>
          ) : error ? (
            <div className="timeline-error">Failed to load history</div>
          ) : history && history.length > 0 ? (
            <div className="timeline-events">
              {history.map((event, index) => (
                <div key={index} className={`timeline-event ${getEventColor(event.event_type)}`}>
                  <div className="event-connector">
                    <div className={`event-dot ${getEventColor(event.event_type)}`}>
                      {getEventIcon(event.event_type)}
                    </div>
                    {index < history.length - 1 && <div className="event-line" />}
                  </div>
                  <div className="event-content">
                    <div className="event-header">
                      <span className="event-label">{formatEventLabel(event.event_type)}</span>
                      <span className="event-timestamp">{formatTimestamp(event.timestamp)}</span>
                    </div>
                    <EventDetails event={event} />
                    {event.actor && (
                      <div className="event-actor">
                        <span className="actor-label">By:</span> {event.actor}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="timeline-empty">No history available</div>
          )}
        </div>
      )}
    </div>
  );
};

export default DocumentTimeline;
