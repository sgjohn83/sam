import { Card } from './Card';

export function StatCard({ title, value, icon: Icon, color = 'primary' }) {
  const colors = {
    primary: 'bg-blue-50 text-blue-600 border-blue-100',
    success: 'bg-green-50 text-green-600 border-green-100',
    warning: 'bg-amber-50 text-amber-600 border-amber-100',
    danger: 'bg-red-50 text-red-600 border-red-100',
  };

  const iconColors = {
    primary: 'bg-blue-600',
    success: 'bg-green-600',
    warning: 'bg-amber-600',
    danger: 'bg-red-600',
  };

  return (
    <Card className="p-0 overflow-hidden border">
      <div className="flex items-stretch">
        <div className={`w-1.5 ${iconColors[color]}`} />
        <div className="p-5 flex-1 flex items-center gap-4">
          <div className={`p-3 rounded-xl ${colors[color]} border`}>
            <Icon className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">{title}</p>
            <p className="text-2xl font-bold text-gray-900 mt-0.5">{value}</p>
          </div>
        </div>
      </div>
    </Card>
  );
}
