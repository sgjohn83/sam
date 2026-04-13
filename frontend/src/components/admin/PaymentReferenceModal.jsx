import React, { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { CreditCard, Loader2, IndianRupee } from 'lucide-react';

export function PaymentReferenceModal({ isOpen, onClose, onConfirm, isPending, amount }) {
  const [reference, setReference] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!reference.trim()) return;
    onConfirm(reference);
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose}
      title="Record Payment Details"
    >
      <form onSubmit={handleSubmit} className="p-6 space-y-6">
        <div className="bg-emerald-50 border border-emerald-100 p-5 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-emerald-600 rounded-lg text-white">
            <IndianRupee size={24} />
          </div>
          <div>
            <p className="text-[10px] text-emerald-600 uppercase font-black tracking-widest">Payout Amount</p>
            <p className="text-2xl font-black text-emerald-900">
               ₹{parseFloat(amount || 0).toLocaleString()}
            </p>
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-bold text-gray-700 flex items-center gap-2">
            <CreditCard size={16} className="text-gray-400" />
            Bank Reference / UTR Number
          </label>
          <Input 
            required
            autoFocus
            className="h-12 text-lg font-mono placeholder:text-gray-300"
            placeholder="e.g. TXN982374612"
            value={reference}
            onChange={(e) => setReference(e.target.value)}
          />
          <p className="text-[10px] text-gray-400 leading-relaxed italic">
            Enter the unique transaction ID provided by your bank to help the agent track this payment.
          </p>
        </div>

        <div className="flex gap-3 justify-end pt-2">
          <Button variant="ghost" type="button" onClick={onClose} disabled={isPending}>
            Cancel
          </Button>
          <Button 
            className="bg-emerald-600 hover:bg-emerald-700 font-bold px-8 h-11 shadow-lg shadow-emerald-100"
            type="submit"
            disabled={!reference.trim() || isPending}
          >
            {isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              'Mark as Paid'
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
