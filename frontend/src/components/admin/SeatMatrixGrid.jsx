import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Save, 
  Upload, 
  ChevronDown, 
  ChevronUp, 
  AlertCircle, 
  CheckCircle,
  X,
  FileText
} from 'lucide-react';
import api from '../../services/api';
import './SeatMatrixGrid.css';

const QUOTA_LABELS = {
  general: 'General',
  obc: 'OBC',
  sc: 'SC',
  st: 'ST',
  management: 'Management',
  nri: 'NRI',
};

const getFillColor = (allocated, total) => {
  if (total === 0) return 'gray';
  const pct = (allocated / total) * 100;
  if (pct >= 100) return 'black';
  if (pct >= 90) return 'red';
  if (pct >= 70) return 'yellow';
  return 'green';
};

export const SeatMatrixGrid = () => {
  const queryClient = useQueryClient();
  const [editMode, setEditMode] = useState({});
  const [editValues, setEditValues] = useState({});
  const [errors, setErrors] = useState({});
  const [expandedRows, setExpandedRows] = useState({});
  const [saveSuccess, setSaveSuccess] = useState(null);

  const { data, isLoading } = useQuery({
    queryKey: ['seat-matrix'],
    queryFn: () => api.get('/admin/seat-matrix/').then(res => res.data),
  });

  const saveMutation = useMutation({
    mutationFn: (items) => api.post('/admin/seat-matrix/', { items }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seat-matrix'] });
      setSaveSuccess('Saved successfully');
      setEditMode({});
      setEditValues({});
      setTimeout(() => setSaveSuccess(null), 3000);
    },
    onError: (err) => {
      const response = err.response?.data;
      if (response?.error) {
        setErrors({ _general: response.error });
      }
    },
  });

  const handleCellClick = (branchId, quota, currentValue) => {
    const key = `${branchId}-${quota}`;
    setEditMode(prev => ({ ...prev, [key]: true }));
    setEditValues(prev => ({ ...prev, [key]: currentValue }));
  };

  const handleCellChange = (branchId, quota, value) => {
    const key = `${branchId}-${quota}`;
    setEditValues(prev => ({ ...prev, [key]: value }));
    setErrors(prev => ({ ...prev, [key]: null }));
  };

  const handleCellBlur = () => {
    setEditMode({});
  };

  const handleCellSave = (branchId, quota) => {
    const key = `${branchId}-${quota}`;
    const value = parseInt(editValues[key], 10);
    if (isNaN(value) || value < 0) {
      setErrors(prev => ({ ...prev, [key]: 'Invalid number' }));
      return;
    }
    const currentRow = data?.branches?.find(b => b.branch_id === branchId);
    const currentCell = currentRow?.quotas?.find(q => q.quota === quota);
    if (currentCell && value < currentCell.allocated) {
      setErrors(prev => ({ ...prev, [key]: `Min: ${currentCell.allocated}` }));
      return;
    }
    const item = {
      branch_id: branchId,
      quota,
      total_seats: value,
    };
    saveMutation.mutate({ items: [item] });
  };

  const handleKeyDown = (e, branchId, quota) => {
    if (e.key === 'Enter') {
      handleCellSave(branchId, quota);
    } else if (e.key === 'Escape') {
      setEditMode({});
    }
  };

  const handleBulkSave = () => {
    const items = Object.keys(editValues).map(key => {
      const [branchId, quota] = key.split('-');
      return {
        branch_id: branchId,
        quota,
        total_seats: parseInt(editValues[key], 10),
      };
    }).filter(item => !isNaN(item.total_seats));
    saveMutation.mutate({ items });
  };

  const toggleRow = (branchId) => {
    setExpandedRows(prev => ({ ...prev, [branchId]: !prev[branchId] }));
  };

  const branches = data?.branches || [];
  const quotas = Object.keys(QUOTA_LABELS);

  if (isLoading) {
    return (
      <div className="seat-matrix-loading">
        <div className="skeleton-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="skeleton" style={{ height: '40px' }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="seat-matrix-container">
      <div className="matrix-header">
        <div>
          <h2>Seat Matrix Configuration</h2>
          <p className="subtitle">{data?.academic_year || 'Current Academic Year'}</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary">
            <Upload size={16} />
            Import CSV
          </button>
          <button 
            className="btn btn-primary"
            onClick={handleBulkSave}
            disabled={Object.keys(editValues).length === 0}
          >
            <Save size={16} />
            Save Changes
          </button>
        </div>
      </div>

      {saveSuccess && (
        <div className="success-banner">
          <CheckCircle size={16} />
          {saveSuccess}
        </div>
      )}

      {errors._general && (
        <div className="error-banner">
          <AlertCircle size={16} />
          {errors._general}
        </div>
      )}

      <div className="matrix-table-wrapper">
        <table className="seat-matrix-table">
          <thead>
            <tr>
              <th className="sticky-col">Branch</th>
              {quotas.map(q => (
                <th key={q} className="quota-col">{QUOTA_LABELS[q]}</th>
              ))}
              <th>Total</th>
              <th>History</th>
            </tr>
          </thead>
          <tbody>
            {branches.map(branch => {
              const branchTotal = branch.quotas?.reduce((sum, q) => sum + q.total, 0) || 0;
              const branchAllocated = branch.quotas?.reduce((sum, q) => sum + q.allocated, 0) || 0;
              return (
                <React.Fragment key={branch.branch_id}>
                  <tr className={expandedRows[branch.branch_id] ? 'expanded' : ''}>
                    <td className="sticky-col branch-name">
                      <span className="branch-code">{branch.branch_code}</span>
                      <span className="branch-name-text">{branch.branch_name}</span>
                    </td>
                    {quotas.map(quota => {
                      const cell = branch.quotas?.find(q => q.quota === quota);
                      const total = cell?.total || 0;
                      const allocated = cell?.allocated || 0;
                      const key = `${branch.branch_id}-${quota}`;
                      const fillColor = getFillColor(allocated, total);
                      return (
                        <td 
                          key={quota}
                          className={`seats-cell ${editMode[key] ? 'editing' : ''}`}
                          onClick={() => !editMode[key] && handleCellClick(branch.branch_id, quota, total)}
                        >
                          {editMode[key] ? (
                            <div className="edit-input-wrapper">
                              <input
                                type="number"
                                value={editValues[key] || ''}
                                onChange={(e) => handleCellChange(branch.branch_id, quota, e.target.value)}
                                onBlur={() => handleCellBlur()}
                                onKeyDown={(e) => handleKeyDown(e, branch.branch_id, quota)}
                                onClick={(e) => e.stopPropagation()}
                                autoFocus
                                min={allocated}
                              />
                              {errors[key] && <span className="cell-error">{errors[key]}</span>}
                            </div>
                          ) : (
                            <div className={`seats-display ${fillColor}`}>
                              {allocated} / {total}
                            </div>
                          )}
                        </td>
                      );
                    })}
                    <td className="total-col">
                      <span className={getFillColor(branchAllocated, branchTotal)}>
                        {branchAllocated} / {branchTotal}
                      </span>
                    </td>
                    <td className="history-col">
                      <button 
                        className="history-btn"
                        onClick={() => toggleRow(branch.branch_id)}
                      >
                        <FileText size={14} />
                        {expandedRows[branch.branch_id] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>
                    </td>
                  </tr>
                  {expandedRows[branch.branch_id] && (
                    <tr className="history-row">
                      <td colSpan={quotas.length + 3}>
                        <div className="history-content">
                          <h4>Change History</h4>
                          <div className="history-list">
                            <p className="empty-history">No recent changes</p>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="legend">
        <span><span className="dot green" /> &lt;70%</span>
        <span><span className="dot yellow" /> 70-90%</span>
        <span><span className="dot red" /> 90-100%</span>
        <span><span className="dot black" /> 100%</span>
      </div>
    </div>
  );
};

export default SeatMatrixGrid;