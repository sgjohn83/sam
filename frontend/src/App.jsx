import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ROUTES } from './constants/routes';
import { ProtectedRoute } from './routes/ProtectedRoute';
import { GuestRoute } from './routes/GuestRoute';
import { AgentRoutes } from './routes/AgentRoutes';
import { PrincipalRoutes } from './routes/PrincipalRoutes';
import { VerifyOTPPage } from './pages/auth/VerifyOtpPage';
import { MainLayout } from './components/layout/MainLayout';

// Mock components for skeleton routes
const Login = () => <h1>Login Page</h1>;
const Register = () => <h1>Register Page</h1>;
const Dashboard = () => <h1>Dashboard</h1>;
const NotFound = () => <h1>404 - Not Found</h1>;
const Unauthorized = () => <h1>403 - Unauthorized</h1>;

import { CommissionManagement } from './pages/admin/CommissionManagement';
import { AgentDashboard } from './pages/agent/AgentDashboard';
import { AgentStudentList } from './pages/agent/AgentStudentList';
import { AgentRegisterStudent } from './pages/agent/AgentRegisterStudent';
import { AgentCommissions } from './pages/agent/AgentCommissions';
import { AgentProfile } from './pages/agent/AgentProfile';
import { PrincipalDashboard } from './pages/principal/PrincipalDashboard';
import { SeatMatrix } from './pages/principal/SeatMatrix';
import { RevenueReport } from './pages/principal/RevenueReport';
import { AgentPerformance } from './pages/principal/AgentPerformance';
import { VerificationPerformance } from './pages/principal/VerificationPerformance';
import { AdminCommissions } from './pages/principal/AdminCommissions';
import { AuditTrail } from './pages/principal/AuditTrail';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

import { GoogleOAuthProvider } from '@react-oauth/google';

function App() {
  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <BrowserRouter>
            <Toaster />
            <Routes>
              {/* Guest Routes */}
              <Route element={<GuestRoute />}>
                <Route path={ROUTES.AUTH.LOGIN} element={<Login />} />
                <Route path={ROUTES.AUTH.REGISTER} element={<Register />} />
                <Route path={ROUTES.AUTH.VERIFY_OTP} element={<VerifyOTPPage />} />
              </Route>

              {/* Protected Routes */}
              <Route element={<ProtectedRoute />}>
                <Route element={<MainLayout />}>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/unauthorized" element={<Unauthorized />} />

                    {/* Agent Specific Routes */}
                    <Route element={<AgentRoutes />}>
                        <Route path="/agent/dashboard" element={<AgentDashboard />} />
                        <Route path="/agent/students" element={<AgentStudentList />} />
                        <Route path="/agent/students/register" element={<AgentRegisterStudent />} />
                        <Route path="/agent/commissions" element={<AgentCommissions />} />
                        <Route path="/agent/profile" element={<AgentProfile />} />
                    </Route>

                    {/* Admin Specific Routes */}
                    <Route element={<ProtectedRoute allowedRoles={['admin', 'principal']} />}>
                        <Route path="/admin/commissions" element={<CommissionManagement />} />
                    </Route>

                    <Route element={<PrincipalRoutes />}>
                        <Route path="/principal/dashboard" element={<PrincipalDashboard />} />
                        <Route path="/principal/seats" element={<SeatMatrix />} />
                        <Route path="/principal/revenue" element={<RevenueReport />} />
                        <Route path="/principal/agents" element={<AgentPerformance />} />
                        <Route path="/principal/verification" element={<VerificationPerformance />} />
                        <Route path="/principal/commissions" element={<AdminCommissions />} />
                        <Route path="/principal/audit-trail" element={<AuditTrail />} />
                    </Route>
                </Route>
              </Route>

              {/* Catch-all */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </QueryClientProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
