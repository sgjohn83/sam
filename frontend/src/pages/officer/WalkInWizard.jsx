import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { 
  User, 
  FileText, 
  CheckCircle, 
  Users, 
  CreditCard,
  ChevronRight,
  ChevronLeft,
  Upload,
  Loader,
  AlertCircle,
  Check,
  X,
  Printer
} from 'lucide-react';
import api from '../../services/api';
import { officerApi } from '../../services/officerApi';
import { FeeBreakdownCard } from '../../components/shared/FeeBreakdownCard';
import './WalkInWizard.css';

const STEPS = [
  { id: 1, title: 'Student Registration', icon: User },
  { id: 2, title: 'Document Scanning', icon: FileText },
  { id: 3, title: 'Verify & Lock', icon: CheckCircle },
  { id: 4, title: 'Allocate Seat', icon: Users },
  { id: 5, title: 'Fee & Complete', icon: CreditCard },
];

const DOCUMENT_TYPES = [
  { key: 'aadhar', label: 'Aadhar Card', required: true },
  { key: 'marksheet_10', label: '10th Marksheet', required: true },
  { key: 'marksheet_12', label: '12th Marksheet', required: true },
  { key: 'rank_card', label: 'Rank Card', required: false },
];

const QUOTA_LABELS = {
  general: 'General',
  obc: 'OBC',
  sc: 'SC',
  st: 'ST',
  management: 'Management',
  nri: 'NRI',
};

export const WalkInWizard = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState(1);
  const [applicationData, setApplicationData] = useState(null);
  const [documents, setDocuments] = useState({});
  const [editedFields, setEditedFields] = useState({});
  const [selectedBranch, setSelectedBranch] = useState(null);
  const [selectedQuota, setSelectedQuota] = useState(null);
  const [feeDeadlineDays, setFeeDeadlineDays] = useState(7);
  const [isComplete, setIsComplete] = useState(false);

  const { data: availability } = useQuery({
    queryKey: ['seat-availability'],
    queryFn: () => api.get('/seats/availability/').then(res => res.data),
    enabled: currentStep === 4,
  });

  const registerMutation = useMutation({
    mutationFn: (data) => api.post('/student/application/walkin/register/', data),
    onSuccess: (res) => {
      setApplicationData(res.data);
      setCurrentStep(2);
    },
  });

  const uploadMutation = useMutation({
    mutationFn: ({ docType, file }) => {
      const formData = new FormData();
      formData.append('document_type', docType);
      formData.append('file', file);
      return api.post(`/student/application/walkin/${applicationData.application_id}/documents/scan/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: (res, { docType }) => {
      setDocuments(prev => ({ ...prev, [docType]: res.data }));
      pollOCRStatus(docType, res.data.document_id);
    },
  });

  const pollOCRStatus = async (docType, docId) => {
    const poll = async () => {
      try {
        const res = await api.get(`/student/application/walkin/${applicationData.application_id}/documents/${docId}/ocr-status/`);
        if (res.data.status === 'completed') {
          setDocuments(prev => ({ 
            ...prev, 
            [docType]: { ...prev[docType], ...res.data, status: 'completed' } 
          }));
          return true;
        }
        if (res.data.status === 'failed') {
          setDocuments(prev => ({ 
            ...prev, 
            [docType]: { ...prev[docType], status: 'failed' } 
          }));
          return true;
        }
      } catch (e) { console.error(e); }
      return false;
    };
    
    for (let i = 0; i < 30; i++) {
      if (await poll()) break;
      await new Promise(r => setTimeout(r, 2000));
    }
  };

  const verifyMutation = useMutation({
    mutationFn: () => {
      const docs = Object.entries(documents).map(([docType, doc]) => ({
        document_id: doc.document_id,
        fields: editedFields[docType] || {},
      }));
      return api.post(`/student/application/walkin/${applicationData.application_id}/verify/`, { documents: docs });
    },
    onSuccess: (res) => {
      setApplicationData(prev => ({ ...prev, ...res.data }));
      setCurrentStep(4);
    },
  });

  const allocateMutation = useMutation({
    mutationFn: () => api.post(`/student/application/walkin/${applicationData.application_id}/allocate-and-notify/`, {
      branch_id: selectedBranch,
      quota: selectedQuota,
      fee_deadline_days: feeDeadlineDays,
    }),
    onSuccess: (res) => {
      setApplicationData(prev => ({ ...prev, ...res.data }));
      setCurrentStep(5);
    },
  });

  const handleFieldEdit = (docType, field, value) => {
    setEditedFields(prev => ({
      ...prev,
      [docType]: { ...(prev[docType] || {}), [field]: value },
    }));
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1: return registerMutation.isIdle || registerMutation.isSuccess;
      case 2: return Object.keys(documents).length >= 3;
      case 3: return verifyMutation.isSuccess;
      case 4: return selectedBranch && selectedQuota;
      case 5: return isComplete;
      default: return false;
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1: return <RegistrationStep 
        onSubmit={(data) => registerMutation.mutate(data)} 
        isLoading={registerMutation.isPending}
        error={registerMutation.error}
      />;
      case 2: return <DocumentScanStep 
        documents={documents}
        editedFields={editedFields}
        onUpload={(docType, file) => uploadMutation.mutate({ docType, file })}
        onFieldEdit={handleFieldEdit}
        isUploading={uploadMutation.isPending}
      />;
      case 3: return <VerifyStep 
        documents={documents}
        editedFields={editedFields}
        applicationData={applicationData}
        onVerify={() => verifyMutation.mutate()}
        isVerifying={verifyMutation.isPending}
      />;
      case 4: return <AllocateStep 
        availability={availability}
        selectedBranch={selectedBranch}
        selectedQuota={selectedQuota}
        onSelect={(branch, quota) => { setSelectedBranch(branch); setSelectedQuota(quota); }}
        onAllocate={() => allocateMutation.mutate()}
        isAllocating={allocateMutation.isPending}
      />;
      case 5: return <FeeStep 
        applicationData={applicationData}
        feeDeadlineDays={feeDeadlineDays}
        onDeadlineChange={setFeeDeadlineDays}
        onComplete={() => setIsComplete(true)}
        onUpdateApplicationData={(updates) => setApplicationData(prev => ({ ...prev, ...updates }))}
      />;
      default: return null;
    }
  };

  return (
    <div className="walkin-wizard">
      <div className="wizard-header">
        <h1>New Walk-In Admission</h1>
        <button className="btn-close" onClick={() => navigate('/officer')}>
          <X size={20} />
        </button>
      </div>

      <div className="wizard-steps">
        {STEPS.map((step, idx) => {
          const Icon = step.icon;
          const isActive = currentStep === step.id;
          const isCompleted = currentStep > step.id;
          return (
            <div key={step.id} className={`step-item ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}>
              <div className="step-icon">
                {isCompleted ? <Check size={16} /> : <Icon size={16} />}
              </div>
              <span className="step-title">{step.title}</span>
              {idx < STEPS.length - 1 && <div className="step-connector" />}
            </div>
          );
        })}
      </div>

      <div className="wizard-content">
        {renderStep()}
      </div>

      <div className="wizard-footer">
        {currentStep > 1 && currentStep < 5 && (
          <button className="btn-secondary" onClick={() => setCurrentStep(s => s - 1)}>
            <ChevronLeft size={18} /> Back
          </button>
        )}
        {currentStep < 5 && (
          <button 
            className="btn-primary" 
            disabled={!canProceed() || currentStep === 2 && Object.keys(documents).length < 3}
            onClick={() => setCurrentStep(s => s + 1)}
          >
            Continue <ChevronRight size={18} />
          </button>
        )}
        {currentStep === 5 && isComplete && (
          <button className="btn-secondary" onClick={() => navigate('/officer')}>
            Return to Dashboard
          </button>
        )}
      </div>
    </div>
  );
};

const RegistrationStep = ({ onSubmit, isLoading, error }) => {
  const [formData, setFormData] = useState({
    full_name: '', email: '', phone: '', date_of_birth: '', gender: '',
    category: '', domicile_state: '', branch_preferences: [],
  });
  const [branches, setBranches] = useState([]);

  useQuery({
    queryKey: ['branches'],
    queryFn: () => api.get('/branches/').then(res => res.data),
    onSuccess: (data) => setBranches(data.map(b => ({ id: b.id, name: b.name, code: b.code }))),
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const toggleBranch = (branchId) => {
    setFormData(prev => ({
      ...prev,
      branch_preferences: prev.branch_preferences.includes(branchId)
        ? prev.branch_preferences.filter(id => id !== branchId)
        : [...prev.branch_preferences, branchId],
    }));
  };

  return (
    <div className="step-content">
      <h2>Student Registration</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-group">
            <label>Full Name *</label>
            <input 
              type="text" 
              value={formData.full_name}
              onChange={e => setFormData(p => ({ ...p, full_name: e.target.value }))}
              required 
            />
          </div>
          <div className="form-group">
            <label>Email *</label>
            <input 
              type="email" 
              value={formData.email}
              onChange={e => setFormData(p => ({ ...p, email: e.target.value }))}
              required 
            />
          </div>
          <div className="form-group">
            <label>Phone *</label>
            <input 
              type="tel" 
              value={formData.phone}
              onChange={e => setFormData(p => ({ ...p, phone: e.target.value }))}
              required 
            />
          </div>
          <div className="form-group">
            <label>Date of Birth *</label>
            <input 
              type="date" 
              value={formData.date_of_birth}
              onChange={e => setFormData(p => ({ ...p, date_of_birth: e.target.value }))}
              required 
            />
          </div>
          <div className="form-group">
            <label>Gender *</label>
            <select value={formData.gender} onChange={e => setFormData(p => ({ ...p, gender: e.target.value }))} required>
              <option value="">Select</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div className="form-group">
            <label>Category *</label>
            <select value={formData.category} onChange={e => setFormData(p => ({ ...p, category: e.target.value }))} required>
              <option value="">Select</option>
              <option value="General">General</option>
              <option value="OBC">OBC</option>
              <option value="SC">SC</option>
              <option value="ST">ST</option>
            </select>
          </div>
          <div className="form-group">
            <label>Domicile State *</label>
            <input 
              type="text" 
              value={formData.domicile_state}
              onChange={e => setFormData(p => ({ ...p, domicile_state: e.target.value }))}
              required 
            />
          </div>
        </div>

        <div className="form-group full-width">
          <label>Branch Preferences * (select at least 1)</label>
          <div className="branch-chips">
            {branches.map(branch => (
              <button
                key={branch.id}
                type="button"
                className={`branch-chip ${formData.branch_preferences.includes(branch.id) ? 'selected' : ''}`}
                onClick={() => toggleBranch(branch.id)}
              >
                {branch.code} - {branch.name}
              </button>
            ))}
          </div>
        </div>

        {error && <div className="error-message">{error.response?.data?.error}</div>}

        <button type="submit" className="btn-primary" disabled={isLoading || formData.branch_preferences.length === 0}>
          {isLoading ? <Loader className="spinner" size={18} /> : 'Register & Continue'}
        </button>
      </form>
    </div>
  );
};

const DocumentScanStep = ({ documents, editedFields, onUpload, onFieldEdit, isUploading }) => {
  const getConfidenceColor = (score) => {
    if (score >= 0.9) return 'green';
    if (score >= 0.7) return 'yellow';
    return 'red';
  };

  return (
    <div className="step-content">
      <h2>Document Scanning</h2>
      <p className="step-description">Upload and scan documents. OCR will extract fields automatically.</p>
      
      <div className="document-grid">
        {DOCUMENT_TYPES.map(doc => {
          const docData = documents[doc.key];
          const isUploaded = !!docData;
          const isProcessing = isUploaded && docData.status === 'processing';
          const isComplete = isUploaded && docData.status === 'completed';
          
          return (
            <div key={doc.key} className={`document-card ${isComplete ? 'complete' : ''}`}>
              <h4>{doc.label}</h4>
              
              {!isUploaded ? (
                <label className="upload-btn">
                  <Upload size={18} /> Upload/Scan
                  <input 
                    type="file" 
                    accept="image/*,.pdf"
                    onChange={e => e.target.files[0] && onUpload(doc.key, e.target.files[0])}
                    hidden 
                  />
                </label>
              ) : isProcessing ? (
                <div className="processing">
                  <Loader className="spinner" size={24} />
                  <span>Processing OCR...</span>
                </div>
              ) : isComplete && docData.fields && (
                <div className="extracted-fields">
                  {Object.entries(docData.fields).slice(0, 5).map(([field, value]) => (
                    <div key={field} className="field-row">
                      <span className="field-name">{field.replace(/_/g, ' ')}</span>
                      <input 
                        type="text" 
                        value={editedFields[doc.key]?.[field] ?? value}
                        onChange={e => onFieldEdit(doc.key, field, e.target.value)}
                        className="field-input"
                      />
                      <span className={`confidence ${getConfidenceColor(docData.confidence_scores?.[field] || 0.8)}`}>
                        {Math.round((docData.confidence_scores?.[field] || 0.8) * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const VerifyStep = ({ documents, editedFields, applicationData, onVerify, isVerifying }) => {
  return (
    <div className="step-content">
      <h2>Verify & Lock</h2>
      <p className="step-description">Review all documents and lock the application.</p>
      
      <div className="verify-summary">
        <div className="summary-card">
          <h4>Application</h4>
          <p><strong>{applicationData?.application_number}</strong></p>
          <p>Status: {applicationData?.status}</p>
        </div>
        
        <div className="documents-summary">
          {Object.entries(documents).map(([key, doc]) => (
            <div key={key} className="doc-summary-item">
              <CheckCircle size={16} className="check-icon" />
              <span>{DOCUMENT_TYPES.find(d => d.key === key)?.label}</span>
              <span className="confidence-badge">
                {Math.round((doc.overall_confidence || 0.8) * 100)}% confidence
              </span>
            </div>
          ))}
        </div>
      </div>

      <button className="btn-primary" onClick={onVerify} disabled={isVerifying}>
        {isVerifying ? <Loader className="spinner" size={18} /> : 'Verify & Lock Application'}
      </button>
    </div>
  );
};

const AllocateStep = ({ availability, selectedBranch, selectedQuota, onSelect, onAllocate, isAllocating }) => {
  const getAvailable = (branchId, quota) => {
    const branch = availability?.find(b => b.branch_id === branchId);
    const q = branch?.quotas?.find(x => x.quota === quota);
    return q?.available || 0;
  };

  return (
    <div className="step-content">
      <h2>Allocate Seat</h2>
      <p className="step-description">Select branch and quota for the student.</p>
      
      <div className="allocation-options">
        {availability?.map(branch => (
          <div key={branch.branch_id} className="branch-option">
            <h4>{branch.branch_name} ({branch.branch_code})</h4>
            <div className="quota-options">
              {branch.quotas?.map(q => {
                const isSelected = selectedBranch === branch.branch_id && selectedQuota === q.quota;
                const isAvailable = q.available > 0;
                return (
                  <button
                    key={q.quota}
                    className={`quota-btn ${isSelected ? 'selected' : ''} ${!isAvailable ? 'disabled' : ''}`}
                    onClick={() => isAvailable && onSelect(branch.branch_id, q.quota)}
                    disabled={!isAvailable}
                  >
                    <span>{QUOTA_LABELS[q.quota]}</span>
                    <span className="avail">{q.available} seats</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <button 
        className="btn-primary" 
        onClick={onAllocate} 
        disabled={!selectedBranch || !selectedQuota || isAllocating}
      >
        {isAllocating ? <Loader className="spinner" size={18} /> : 'Allocate Seat'}
      </button>
    </div>
  );
};

const FeeStep = ({ applicationData, feeDeadlineDays, onDeadlineChange, onComplete, onUpdateApplicationData }) => {
  const { data: feeBreakdown, isLoading: feeLoading } = useQuery({
    queryKey: ['fee-breakdown', applicationData?.application_id],
    queryFn: () => officerApi.calculateFee(applicationData?.application_id).then(res => res.data),
    enabled: !!applicationData?.application_id,
  });

  const resendFeeMutation = useMutation({
    mutationFn: () => officerApi.resendFeeInstructions(applicationData.application_id),
    onSuccess: (res) => {
      // Update application data with new fee instruction sent timestamp
      onUpdateApplicationData({
        fee_instruction_sent_at: res.data.fee_instruction_sent_at
      });
    },
  });

  if (!applicationData) {
    return (
      <div className="step-content">
        <h2>Fee & Complete</h2>
        <p className="step-description">Loading application data...</p>
      </div>
    );
  }

  const hasFeeInstructionsSent = applicationData.fee_instruction_sent_at;
  const feeDeadlineDate = new Date(applicationData.fee_deadline);
  const isDeadlinePassed = feeDeadlineDate < new Date();

  return (
    <div className="step-content">
      <h2>Fee & Complete</h2>
      <p className="step-description">Review fee details and send instructions.</p>
      
      <div className="fee-summary-grid">
        <div className="fee-summary-card">
          <h4>Admission Summary</h4>
          <div className="summary-row">
            <span>Application Number:</span>
            <strong>{applicationData.application_number}</strong>
          </div>
          <div className="summary-row">
            <span>Branch:</span>
            <strong>{applicationData.allocated_branch}</strong>
          </div>
          <div className="summary-row">
            <span>Quota:</span>
            <strong>{applicationData.allocated_quota}</strong>
          </div>
          <div className="summary-row">
            <span>Payment Reference:</span>
            <strong className="payment-ref">{applicationData.payment_reference_id}</strong>
          </div>
          <div className="summary-row">
            <span>Fee Deadline:</span>
            <strong className={isDeadlinePassed ? 'text-red-600' : ''}>
              {feeDeadlineDate.toLocaleDateString()} {isDeadlinePassed && '(Passed)'}
            </strong>
          </div>
          <div className="summary-row">
            <span>Fee Instructions:</span>
            <strong>
              {hasFeeInstructionsSent 
                ? `Sent ${new Date(applicationData.fee_instruction_sent_at).toLocaleString()}`
                : 'Not sent yet'}
            </strong>
          </div>
        </div>

        <FeeBreakdownCard 
          feeData={feeBreakdown}
          paymentReference={applicationData.payment_reference_id}
          showPaymentReference={false}
          compact={false}
        />
      </div>

      <div className="deadline-setting">
        <label>Update Fee Deadline (days from now):</label>
        <input 
          type="number" 
          value={feeDeadlineDays}
          onChange={e => onDeadlineChange(parseInt(e.target.value))}
          min={1}
          max={30}
        />
        <span className="text-sm text-gray-500">
          Current: {feeDeadlineDate.toLocaleDateString()}
        </span>
      </div>

      {hasFeeInstructionsSent ? (
        <div className="success-message">
          <CheckCircle size={24} />
          <div>
            <h4>Fee Instructions Sent!</h4>
            <p>
              Instructions were sent to student on {new Date(applicationData.fee_instruction_sent_at).toLocaleString()}.
              {isDeadlinePassed && ' Deadline has passed.'}
            </p>
          </div>
        </div>
      ) : (
        <div className="warning-message">
          <AlertCircle size={24} />
          <div>
            <h4>Fee Instructions Not Sent</h4>
            <p>Fee instructions have not been sent to the student yet.</p>
          </div>
        </div>
      )}

      <div className="wizard-actions">
        <button className="btn-secondary" onClick={() => window.print()}>
          <Printer size={18} /> Print Summary
        </button>
        {hasFeeInstructionsSent ? (
          <button 
            className="btn-primary" 
            onClick={() => resendFeeMutation.mutate()}
            disabled={resendFeeMutation.isPending}
          >
            {resendFeeMutation.isPending ? (
              <>
                <Loader className="spinner" size={18} /> Resending...
              </>
            ) : (
              'Resend Fee Instructions'
            )}
          </button>
        ) : (
          <button className="btn-primary" onClick={onComplete}>
            Complete Walk-In
          </button>
        )}
      </div>
    </div>
  );
};

export default WalkInWizard;