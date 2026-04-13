import React, { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { AlertTriangle, Loader2 } from 'lucide-react';

export function CommissionRejectModal({ isOpen, onClose, onConfirm, isPending }) {
  const [reason, setReason] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (reason.length < 20) return;
    onConfirm(reason);
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose}
      title="Reject Commission Record"
    >
      <form onSubmit={handleSubmit} className="p-6 space-y-4">
        <div className="bg-red-50 border border-red-100 p-4 rounded-lg flex gap-3">
          <AlertTriangle className="text-red-600 flex-shrink-0" size={20} />
          <p className="text-xs text-red-700 leading-relaxed">
            Rejecting a commission will notify the agent. Please provide a clear, detailed 
            reason explaining why this referral was disqualified (e.g., student withdrawal, 
            invalid fee structure).
          </p>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-bold text-gray-700 flex justify-between">
            Rejection Reason
            <span className={`text-[10px] ${reason.length < 20 ? 'text-amber-600' : 'text-emerald-600'}`}>
              {reason.length}/20 chars min
            </span>
          </label>
          <textarea 
            required
            className="w-full rounded-lg border-gray-300 text-sm h-32 focus:ring-red-500 focus:border-red-500"
            placeholder="Type at least 20 characters explaining the rejection..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </div>

        <div className="flex gap-3 justify-end pt-2">
          <Button variant="ghost" onClick={onClose} disabled={isPending}>
            Cancel
          </Button>
          <Button 
            variant="danger"
            type="submit"
            className="bg-red-600 hover:bg-red-700 font-bold px-6"
            disabled={reason.length < 20 || isPending}
          >
            {isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Rejecting...
              </>
            ) : (
              'Confirm Rejection'
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
