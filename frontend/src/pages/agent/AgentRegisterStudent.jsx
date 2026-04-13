import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { agentApi } from '../../services/agentApi';
import { authApi } from '../../services/authApi';
import { useAuth } from '../../contexts/AuthContext';
import { PageHeader } from '../../components/layout/PageHeader';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { toast } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';

const schema = z.object({
  full_name: z.string().min(3, 'Name must be at least 3 characters'),
  email: z.string().email('Invalid email'),
  phone: z.string().regex(/^[6-9]\d{9}$/, 'Invalid 10-digit Indian mobile number'),
  category: z.string().optional(),
});

export function AgentRegisterStudent() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isAgentVerified = user?.agent_data?.is_verified;

  const { register, handleSubmit, formState: { errors, isSubmitting }, watch } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      category: 'general',
    }
  });

  const registerMutation = useMutation({
    mutationFn: (data) => agentApi.registerStudent(data),
    onSuccess: () => {
      toast.success('Student registered successfully! Verification email sent.');
      navigate('/agent/students');
    },
    onError: (err) => {
      toast.error(err.response?.data?.error || 'Failed to register student');
    }
  });

  const onSubmit = (data) => {
    registerMutation.mutate({
      full_name: data.full_name,
      email: data.email,
      phone: data.phone,
      category: data.category
    });
  };

  return (
    <div className="p-6 space-y-6 max-w-2xl mx-auto">
      <PageHeader 
        title="Register New Student" 
        subtitle="Create an account and start an application for a new student" 
      />

      {!isAgentVerified && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-3 items-start">
          <AlertCircle className="text-amber-600 w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-amber-800 font-bold text-sm">Account Pending Verification</h4>
            <p className="text-amber-700 text-xs mt-1 leading-relaxed">
              Your agent account is currently under review. You can register students, but their 
              applications will only be processed once your partnership is verified by our team.
            </p>
          </div>
        </div>
      )}

      <Card className="p-8">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-bold text-gray-700">Student Full Name</label>
            <Input 
              {...register('full_name')}
              placeholder="e.g. Rahul Sharma"
              error={errors.full_name?.message}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-bold text-gray-700">Email Address</label>
            <Input 
              {...register('email')}
              type="email"
              placeholder="rahul@example.com"
              error={errors.email?.message}
            />
            <p className="text-[10px] text-gray-400">Student will receive login instructions at this email.</p>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-bold text-gray-700">Mobile Number</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm font-bold font-mono">
                +91
              </span>
              <Input 
                {...register('phone')}
                placeholder="9876543210"
                className="pl-12"
                error={errors.phone?.message}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-bold text-gray-700">Reservation Category</label>
            <select 
              {...register('category')}
              className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
            >
              <option value="general">General (Open)</option>
              <option value="obc">OBC (Other Backward Classes)</option>
              <option value="sc">SC (Scheduled Caste)</option>
              <option value="st">ST (Scheduled Tribe)</option>
            </select>
            {errors.category && <p className="text-red-500 text-xs mt-1">{errors.category.message}</p>}
          </div>

          <div className="pt-4">
            <Button 
              type="submit" 
              className="w-full h-12 text-base font-bold"
              disabled={isSubmitting || registerMutation.isPending}
            >
              {registerMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <CheckCircle2 className="mr-2 h-5 w-5" />
                  Complete Registration
                </>
              )}
            </Button>
          </div>
        </form>
      </Card>

      <div className="text-center">
        <p className="text-sm text-gray-500">
          Already registered? <Link to="/agent/students" className="text-blue-600 font-bold hover:underline">View Student List</Link>
        </p>
      </div>
    </div>
  );
}
