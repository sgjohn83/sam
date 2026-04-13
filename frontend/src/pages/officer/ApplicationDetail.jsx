import React, { useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { officerApi } from '../../services/officerApi';
import {  
  ArrowLeft,  
  User,  
  MapPin,  
  Phone,  
  Mail,  
  Calendar,
  Award,
  FileText,
  CheckCircle,
  Lock,
  Clock,
  Users,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  X,
  ExternalLink,
  Send
} from 'lucide-react';
import { FeeBreakdownCard } from '../../components/shared/FeeBreakdownCard';

const DocumentModal = ({ document, onClose }) => {
  if (!document) return null;

  return (
    <div className="document-modal-overlay" onClick={onClose}>
      <div className="document-modal" onClick={e => e.stopPropagation()}>
        <div className="document-modal-header">
          <h3>{document.document_label}</h3>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        <div className="document-modal-content">
          {document.file_url ? (
            document.mime_type?.startsWith('image/') ? (
              <img src={document.file_url} alt={document.document_label} />
            ) : (
              <iframe src={document.file_url} title={document.document_label} />
            )
          ) : (
            <div className="no-preview">No preview available</div>
          )}
        </div>
        <div className="document-modal-footer">
          <a href={document.file_url} target="_blank" rel="noopener noreferrer" className="external-link">
            <ExternalLink size={16} /> Open in new tab
          </a>
        </div>
      </div>
    </div>
  );
};

const StudentInfoCard = ({ student }) => {
  if (!student) return null;

  return (
    <div className="detail-card">
      <div className="card-header">
        <User size={20} />
        <h3>Student Information</h3>
      </div>
      <div className="card-content">
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Full Name</span>
            <span className="info-value">{student.full_name}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Email</span>
            <span className="info-value">{student.email}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Mobile</span>
            <span className="info-value">{student.mobile_number || '-'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Date of Birth</span>
            <span className="info-value">
              {student.date_of_birth ? new Date(student.date_of_birth).toLocaleDateString() : '-'}
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">Gender</span>
            <span className="info-value">{student.gender || '-'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Category</span>
            <span className="info-value">{student.category || '-'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Domicile State</span>
            <span className="info-value">{student.domicile_state || '-'}</span>
          </div>
          <div className="info-item full-width">
            <span className="info-label">Address</span>
            <span className="info-value">
              {student.address ? `${student.address.street}, ${student.address.city}, ${student.address.state} - ${student.address.pincode}` : '-'}
            </span>
          </div>
          {student.parent_name && (
            <div className="info-item">
              <span className="info-label">Parent Name</span>
              <span className="info-value">{student.parent_name}</span>
            </div>
          )}
          {student.parent_phone && (
            <div className="info-item">
              <span className="info-label">Parent Phone</span>
              <span className="info-value">{student.parent_phone}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const BranchPreferencesCard = ({ preferences }) => {
  return (
    <div className="detail-card">
      <div className="card-header">
        <Award size={20} />
        <h3>Branch Preferences</h3>
      </div>
      <div className="card-content">
        {preferences && preferences.length > 0 ? (
          <ol className="preference-list">
            {preferences.map((branch, index) => (
              <li key={index} className="preference-item">
                <span className="preference-rank">#{index + 1}</span>
                <span className="preference-name">{branch}</span>
              </li>
            ))}
          </ol>
        ) : (
          <p className="no-data">No branch preferences</p>
        )}
      </div>
    </div>
  );
};

const DocumentsCard = ({ documents, onDocumentClick }) => {
  return (
    <div className="detail-card">
      <div className="card-header">
        <FileText size={20} />
        <h3>Documents</h3>
      </div>
      <div className="card-content">
        <div className="documents-grid">
          {documents?.map(doc => (
            <div 
              key={doc.document_id} 
              className={`document-thumbnail ${doc.is_rejected ? 'rejected' : ''} ${doc.status === 'verified' ? 'verified' : ''}`}
              onClick={() => onDocumentClick(doc)}
            >
              <div className="doc-icon">
                <FileText size={24} />
              </div>
              <div className="doc-info">
                <span className="doc-name">{doc.document_label}</span>
                <StatusBadge status={doc.is_rejected ? 'rejected' : doc.status} />
              </div>
              {doc.ocr_confidence && (
                <div className="doc-confidence">
                  {Math.round(doc.ocr_confidence * 100)}% confidence
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const MeritScoreCard = ({ meritScore, breakdown }) => {
  return (
    <div className="detail-card">
      <div className="card-header">
        <Award size={20} />
        <h3>Merit Score</h3>
      </div>
      <div className="card-content">
        <div className="merit-total">
          <span className="merit-value">{meritScore?.toLocaleString() || '-'}</span>
          <span className="merit-label">Total Score</span>
        </div>
        {breakdown && (
          <div className="merit-breakdown">
            <div className="breakdown-item">
              <span className="breakdown-label">Base Score</span>
              <span className="breakdown-value">{breakdown.base_score?.toLocaleString() || 0}</span>
            </div>
            <div className="breakdown-item">
              <span className="breakdown-label">Additional Score</span>
              <span className="breakdown-value">{breakdown.additional_score?.toLocaleString() || 0}</span>
            </div>
            <div className="breakdown-item">
              <span className="breakdown-label">Quota Bonus</span>
              <span className="breakdown-value">{breakdown.quota_bonus || 0}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const StatusCard = ({ application }) => {
  const getStatus = () => {
    if (application.is_locked) return 'locked';
    return application.status;
  };

  return (
    <div className="detail-card">
      <div className="card-header">
        <CheckCircle size={20} />
        <h3>Application Status</h3>
      </div>
      <div className="card-content">
        <div className="status-display">
          <StatusBadge status={getStatus()} />
        </div>
        <div className="status-details">
          {application.submitted_at && (
            <div className="status-item">
              <Clock size={14} />
              <span>Submitted: {new Date(application.submitted_at).toLocaleString()}</span>
            </div>
          )}
          {application.is_locked && (
            <div className="status-item locked">
              <Lock size={14} />
              <span>Locked: {new Date(application.locked_at).toLocaleString()}</span>
            </div>
          )}
          {application.allocated_branch && (
            <div className="status-item">
              <Award size={14} />
              <span>Allocated Branch: {application.allocated_branch}</span>
            </div>
          )}
          {application.allocated_quota && (
            <div className="status-item">
              <span>Quota: {application.allocated_quota}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const AuditTrailPanel = ({ auditTrail }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="audit-panel">
      <button className="audit-toggle" onClick={() => setIsExpanded(!isExpanded)}>
        {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
        <span>Audit Trail ({auditTrail?.length || 0} entries)</span>
      </button>
      
      {isExpanded && (
        <div className="audit-content">
          {auditTrail && auditTrail.length > 0 ? (
            <div className="audit-timeline">
              {auditTrail.map((entry, index) => (
                <div key={entry.id || index} className="audit-entry">
                  <div className="audit-dot" />
                  <div className="audit-entry-content">
                    <div className="audit-entry-header">
                      <span className="audit-action">{entry.action.replace(/_/g, ' ')}</span>
                      <span className="audit-time">
                        {new Date(entry.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="audit-actor">by {entry.actor_email || 'System'}</div>
                    {entry.after_json && (
                      <div className="audit-changes">
                        {Object.entries(entry.after_json).map(([key, value]) => (
                          <span key={key} className="change-item">
                            {key}: {String(value)}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-data">No audit trail available</p>
          )}
        </div>
      )}
    </div>
  );
};

export const ApplicationDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showAllocateModal, setShowAllocateModal] = useState(false);
  const [showDeallocateModal, setShowDeallocateModal] = useState(false);
  const [showFeeModal, setShowFeeModal] = useState(false);
  const [showFeeModalForConfirmation, setShowFeeModalForConfirmation] = useState(false);
  const [showSuccessAnimation, setShowSuccessAnimation] = useState(false);

  const { data: application, isLoading, error } = useQuery({
    queryKey: ['officer-application-detail', id],
    queryFn: () => officerApi.getApplicationDetail(id).then(res => res.data),
  });

  const { data: feeBreakdown } = useQuery({
    queryKey: ['fee-breakdown', id],
    queryFn: () => officerApi.calculateFee(id).then(res => res.data),
    enabled: !!application?.allocated_branch,
  });

  const handleBack = () => {
    const params = new URLSearchParams(location.search);
    navigate(`/officer?${params.toString()}`);
  };

  const handleFeeSuccess = (updatedData) => {
    queryClient.invalidateQueries({ queryKey: ['officer-application-detail', id] });
    queryClient.invalidateQueries({ queryKey: ['officer-applications'] });
    
    if (updatedData?.status === 'admitted') {
      setShowSuccessAnimation(true);
      setTimeout(() => setShowSuccessAnimation(false), 3000);
    }
  };

  const canSendFeeInstructions = application?.status === 'seat_allocated' && application?.allocated_branch;
  const hasFeeInstructions = !!application?.fee_instruction_sent_at;
  const canConfirmPayment = application?.fee_instruction_sent_at && !application?.fee_paid;

  if (isLoading) {
    return (
      <div className="application-detail loading">
        <div className="spinner" />
        <span>Loading application...</span>
      </div>
    );
  }

  if (error || !application) {
    return (
      <div className="application-detail error">
        <p>Failed to load application details</p>
        <button onClick={handleBack}>Back to Dashboard</button>
      </div>
    );
  }

  return (
    <div className="application-detail">
      {showSuccessAnimation && (
        <div className="success-overlay">
          <div className="success-content">
            <div className="success-icon">
              <CheckCircle size={64} />
            </div>
            <h2>Admission Confirmed!</h2>
            <p>Student has been successfully admitted.</p>
          </div>
          <div className="confetti">
            {[...Array(50)].map((_, i) => (
              <div key={i} className="confetti-piece" style={{
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 2}s`,
                backgroundColor: ['#25d9eb', '#15a34a', '#f59e0b', '#ef4444', '#8b5cf6'][Math.floor(Math.random() * 5)]
              }} />
            ))}
          </div>
        </div>
      )}
      
      <div className="detail-header">
        <button className="back-button" onClick={handleBack}>
          <ArrowLeft size={18} />
          Back to List
        </button>
        <div className="header-title">
          <h1>{application.application_number}</h1>
          <StatusBadge status={application.is_locked ? 'locked' : application.status} />
        </div>
      </div>

      <div className="detail-grid">
        <StudentInfoCard student={application.student_profile} />
        
        <div className="detail-sidebar">
          <StatusCard application={application} />
          <MeritScoreCard 
            meritScore={application.merit_score} 
            breakdown={application.merit_breakdown} 
          />
        </div>
      </div>

      <BranchPreferencesCard preferences={application.branch_preferences} />
      
      {feeBreakdown && (
        <div className="fee-breakdown-section">
          <FeeBreakdownCard 
            feeData={feeBreakdown}
            paymentReference={application.payment_reference_id}
            showPaymentReference={true}
            compact={false}
          />
        </div>
      )}
      
      <div className="action-buttons">
        {canSendFeeInstructions && (
          <button className="btn-fee" onClick={() => {
            setShowFeeModalForConfirmation(false);
            setShowFeeModal(true);
          }}>
            <Send size={18} />
            {hasFeeInstructions ? (
              <>
                Resend
                {application.fee_instruction_sent_at && (
                  <span className="fee-sent-time">
                    (Sent {new Date(application.fee_instruction_sent_at).toLocaleDateString()})
                  </span>
                )}
              </>
            ) : 'Send Fee Instructions'}
          </button>
        )}
        {!application.allocated_branch && application.status === 'verified' && (
          <button className="btn-allocate" onClick={() => setShowAllocateModal(true)}>
            <Users size={18} />
            Allocate Seat
          </button>
        )}
        {application.allocated_branch && (
          <button className="btn-deallocate" onClick={() => setShowDeallocateModal(true)}>
            <AlertCircle size={18} />
            Deallocate
          </button>
        )}
        {canConfirmPayment && (
          <button className="btn-confirm-payment" onClick={() => {
            setShowFeeModalForConfirmation(true);
            setShowFeeModal(true);
          }}>
            <CheckCircle size={18} />
            Confirm Payment
          </button>
        )}
      </div>

      <DocumentsCard 
        documents={application.documents} 
        onDocumentClick={setSelectedDocument}
      />

      <AuditTrailPanel auditTrail={application.audit_trail} />

      {selectedDocument && (
        <DocumentModal 
          document={selectedDocument} 
          onClose={() => setSelectedDocument(null)} 
        />
      )}

      {showAllocateModal && (
        <AllocationModal 
          application={application} 
          onClose={() => setShowAllocateModal(false)} 
        />
      )}

      {showDeallocateModal && (
        <DeallocateModal 
          application={application} 
          onClose={() => setShowDeallocateModal(false)} 
        />
      )}

      {showFeeModal && (
        <FeeModal 
          application={application} 
          onClose={() => {
            setShowFeeModal(false);
            setShowFeeModalForConfirmation(false);
          }}
          onSuccess={handleFeeSuccess}
          showConfirmPayment={showFeeModalForConfirmation}
        />
      )}
    </div>
  );
};

export default ApplicationDetail;