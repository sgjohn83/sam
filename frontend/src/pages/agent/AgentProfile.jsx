import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { agentApi } from '../../services/agentApi';
import { PageHeader } from '../../components/layout/PageHeader';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { badge as Badge } from '../../components/ui/Badge'; // assuming badge component is available
import { 
  Building2, 
  CreditCard, 
  User, 
  MapPin, 
  Phone, 
  CheckCircle2, 
  AlertCircle,
  Loader2,
  Save,
  ShieldCheck,
  TrendingUp
} from 'lucide-react';
import { toast } from 'react-hot-toast';

const profileSchema = z.object({
  agency_name: z.string().min(3, 'Agency name is required'),
  contact_phone: z.string().regex(/^[6-9]\d{9}$/, 'Invalid 10-digit mobile number'),
  address: z.string().min(10, 'Full address is required'),
  pan_number: z.string().regex(/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/, 'Invalid PAN format'),
  bank_account_name: z.string().min(3, 'Account holder name is required'),
  bank_account_number: z.string().min(9, 'Valid account number is required'),
  bank_ifsc: z.string().regex(/^[A-Z]{4}0[A-Z0-9]{6}$/, 'Invalid IFSC code format'),
});

export function AgentProfile() {
  const queryClient = useQueryClient();
  const { data: profile, isLoading } = useQuery({
    queryKey: ['agent-profile'],
    queryFn: () => agentApi.getProfile().then(r => r.data),
  });

  const { register, handleSubmit, reset, formState: { errors, isDirty } } = useForm({
    resolver: zodResolver(profileSchema),
  });

  // Re-sync form when data is fetched
  React.useEffect(() => {
    if (profile) {
      reset({
        agency_name: profile.agency_name || '',
        contact_phone: profile.contact_phone || '',
        address: profile.address || '',
        pan_number: profile.pan_number || '',
        bank_account_name: profile.bank_account_name || '',
        bank_account_number: profile.bank_account_number || '',
        bank_ifsc: profile.bank_ifsc || '',
      });
    }
  }, [profile, reset]);

  const updateMutation = useMutation({
    mutationFn: (data) => agentApi.updateProfile(data),
    onSuccess: () => {
      toast.success('Profile updated successfully');
      queryClient.invalidateQueries(['agent-profile']);
    },
    onError: (err) => {
      toast.error(err.response?.data?.error || 'Failed to update profile');
    }
  });

  if (isLoading) return (
    <div className="p-8 flex items-center justify-center">
      <Loader2 className="animate-spin text-blue-600 w-8 h-8" />
    </div>
  );

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <PageHeader 
        title="Agency Profile" 
        subtitle="Manage your business information and bank details for payouts." 
      />

      {!profile.is_verified && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 flex gap-4 items-start shadow-sm">
          <div className="p-2 bg-white rounded-lg text-amber-600 shadow-sm border border-amber-100">
            <AlertCircle size={20} />
          </div>
          <div>
            <h4 className="text-amber-800 font-bold mb-1">Account Under Review</h4>
            <p className="text-amber-700 text-sm leading-relaxed">
              Your partnership agreement is currently being verified. Please ensure your <strong>Bank Details</strong> 
              are accurate, as they are mandatory for commission payouts.
            </p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit((data) => updateMutation.mutate(data))} className="space-y-6 pb-20">
        
        {/* Section 1: Business Identity */}
        <Card className="p-6 space-y-6 border-slate-200">
          <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
              <Building2 size={20} />
            </div>
            <h3 className="font-black text-gray-900 uppercase tracking-wider text-sm">Business Identity</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-xs font-black text-slate-500 uppercase tracking-tight">Agency Name</label>
              <Input {...register('agency_name')} error={errors.agency_name?.message} />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-black text-slate-500 uppercase tracking-tight">Email (Primary)</label>
              <Input value={profile.email} disabled className="bg-slate-50 text-slate-500 cursor-not-allowed" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-black text-slate-500 uppercase tracking-tight">Contact Phone</label>
              <div className="relative">
                <Phone size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <Input {...register('contact_phone')} className="pl-9" error={errors.contact_phone?.message} />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-black text-slate-500 uppercase tracking-tight">Verification Status</label>
              <div className={`h-10 px-3 rounded-lg flex items-center gap-2 font-bold text-sm border ${profile.is_verified ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : 'bg-slate-50 text-slate-500 border-slate-100'}`}>
                {profile.is_verified ? <ShieldCheck size={16} /> : <Loader2 size={16} className="animate-spin" />}
                {profile.is_verified ? 'Verified Partner' : 'Verification In-Progress'}
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-black text-slate-500 uppercase tracking-tight">Office Address</label>
            <div className="relative">
              <MapPin size={14} className="absolute left-3 top-3 text-slate-400" />
              <textarea 
                {...register('address')}
                className={`w-full h-24 pl-9 rounded-lg border-slate-200 text-sm focus:ring-blue-500 focus:border-blue-500 ${errors.address ? 'border-red-500' : ''}`}
                placeholder="Full business address with Pincode..."
              />
              {errors.address && <p className="text-red-500 text-xs mt-1">{errors.address.message}</p>}
            </div>
          </div>
        </Card>

        {/* Section 2: Banking & Tax */}
        <Card className="p-6 space-y-6 border-slate-200">
          <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <CreditCard size={20} />
            </div>
            <h3 className="font-black text-gray-900 uppercase tracking-wider text-sm">Banking & Tax</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-xs font-black text-slate-500 uppercase tracking-tight">PAN Card Number</label>
              <Input {...register('pan_number')} placeholder="ABCDE1234F" className="uppercase font-mono" error={errors.pan_number?.message} />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-black text-slate-500 uppercase tracking-tight">Account Holder Name</label>
              <Input {...register('bank_account_name')} error={errors.bank_account_name?.message} />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-black text-slate-500 uppercase tracking-tight">Bank Account Number</label>
              <Input {...register('bank_account_number')} type="password" error={errors.bank_account_number?.message} />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-black text-slate-500 uppercase tracking-tight">Bank IFSC Code</label>
              <Input {...register('bank_ifsc')} placeholder="HDFC0001234" className="uppercase font-mono" error={errors.bank_ifsc?.message} />
            </div>
          </div>
        </Card>

        {/* Section 3: Partnership Metrics */}
        <Card className="p-6 space-y-6 border-slate-200 bg-slate-50/50">
          <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <TrendingUp size={20} />
            </div>
            <h3 className="font-black text-gray-900 uppercase tracking-wider text-sm">Partnership Metrics</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
              <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-1">Standard Commission Rate</p>
              <p className="text-2xl font-black text-indigo-600">{profile.commission_rate}%</p>
              <p className="text-[10px] text-slate-400 mt-1 italic">Rate is set by University Administration</p>
            </div>
            <div className="p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
              <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-1">Total Lifetime Earnings</p>
              <p className="text-2xl font-black text-emerald-600">₹{parseFloat(profile.total_commission_earned || 0).toLocaleString()}</p>
              <p className="text-[10px] text-slate-400 mt-1 italic">Inclusive of all processed payouts</p>
            </div>
          </div>
        </Card>

        {/* FAB Style Save Button */}
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-30">
          <Button 
            variant="primary" 
            type="submit"
            className={`shadow-2xl shadow-blue-400 px-8 h-14 rounded-full font-black text-lg gap-2 transition-all duration-300 ${isDirty ? 'scale-105' : 'opacity-60 grayscale'}`}
            disabled={updateMutation.isPending || !isDirty}
          >
            {updateMutation.isPending ? (
              <Loader2 className="animate-spin" />
            ) : (
              <Save size={20} />
            )}
            Save Changes
          </Button>
        </div>
      </form>
    </div>
  );
}
