import { GoogleLogin } from '@react-oauth/google';
import { Card } from '../../components/ui/Card';
import { ROUTES } from '../../constants/routes';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { authApi } from '../../services/authApi';
import toast from 'react-hot-toast';

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSuccess = async (credentialResponse) => {
    try {
      const response = await authApi.googleLogin(credentialResponse.credential);
      login(response.data);
      // getHomeRoute helper would be used here
      navigate('/');
    } catch (error) {
      toast.error('Google sign-in failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
      <Card className="w-full max-w-md text-center">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-primary">Admission Portal</h1>
          <p className="text-gray-600 mt-2">Smart & Automated Admission System</p>
        </div>
        
        <div className="flex justify-center mb-4">
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={() => toast.error('Google sign-in failed')}
          />
        </div>

        <div className="text-sm text-gray-600">
          Don't have an account?{' '}
          <button onClick={() => navigate(ROUTES.AUTH.REGISTER)} className="text-primary hover:underline font-medium">
            Register with Email
          </button>
        </div>
      </Card>
    </div>
  );
};
