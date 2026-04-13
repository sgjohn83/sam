import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { authApi } from '../../services/authApi';
import { useAuth } from '../../contexts/AuthContext';
import { getHomeRoute } from '../../utils/roleRedirect';

export const VerifyOTPPage = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [cooldown, setCooldown] = useState(60);
  const inputs = useRef([]);

  useEffect(() => {
    if (!state?.email) navigate('/register');
    const timer = cooldown > 0 && setInterval(() => setCooldown(cooldown - 1), 1000);
    return () => clearInterval(timer);
  }, [cooldown, navigate, state]);

  const handleChange = (index, value) => {
    if (isNaN(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    if (value && index < 5) inputs.current[index + 1].focus();
  };

  const handleVerify = async () => {
    try {
      const response = await authApi.verifyOtp({ email: state.email, code: otp.join('') });
      toast.success('Verification successful');
      // After success, we might need a separate login or session refresh
      // For now, redirecting based on role logic if possible
      window.location.reload(); // Refresh to trigger auth check
    } catch (error) {
      toast.error(error.response?.data?.error || 'Verification failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
      <Card className="w-full max-w-md text-center">
        <h2 className="text-xl font-bold mb-4">Verify OTP</h2>
        <p className="text-gray-600 mb-6">Sent to {state?.email}</p>
        <div className="flex justify-center gap-2 mb-6">
          {otp.map((digit, i) => (
            <input
              key={i}
              ref={el => inputs.current[i] = el}
              type="text"
              maxLength={1}
              value={digit}
              onChange={(e) => handleChange(i, e.target.value)}
              className="w-10 h-12 text-center border rounded-lg text-lg font-bold focus:ring-primary"
            />
          ))}
        </div>
        <Button onClick={handleVerify} className="w-full mb-4">Verify</Button>
        <button 
          disabled={cooldown > 0} 
          onClick={() => authApi.register(state.email)}
          className="text-primary hover:underline text-sm disabled:text-gray-400"
        >
          {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend OTP'}
        </button>
      </Card>
    </div>
  );
};
