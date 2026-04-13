import { PageHeader } from '../../components/layout/PageHeader';
import { Card } from '../../components/ui/Card';
import { useAuth } from '../../contexts/AuthContext';

export const StudentDashboard = () => {
  const { user } = useAuth();
  return (
    <>
      <PageHeader title={`Welcome, ${user?.full_name || 'Student'}`} />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>Application Status: Pending</Card>
        <Card>Documents Uploaded: 2/4</Card>
        <Card>Seats Allocated: None</Card>
      </div>
    </>
  );
};
