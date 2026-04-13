import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card } from '../../components/ui/Card';
import { ROUTES } from '../../constants/routes';
import { authApi } from '../../services/authApi';

const schema = z.object({
  email: z.string().email('Invalid email address'),
});

export const RegisterPage = () => {
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data) => {
    try {
      await authApi.register(data.email);
      toast.success('OTP sent to your email');
      navigate(ROUTES.AUTH.VERIFY_OTP, { state: { email: data.email } });
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to send OTP');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
      <Card className="w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center text-primary">Register</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input 
            {...register('email')}
            label="Email Address"
            error={errors.email?.message}
            placeholder="student@college.edu"
          />
          <Button type="submit" className="w-full" loading={isSubmitting}>
            Send OTP
          </Button>
        </form>
        <div className="text-center mt-4 text-sm text-gray-600">
          Already have an account?{' '}
          <button onClick={() => navigate(ROUTES.AUTH.LOGIN)} className="text-primary hover:underline font-medium">
            Sign in
          </button>
        </div>
      </Card>
    </div>
  );
};
