export const Badge = ({ children, variant = 'neutral' }) => {
  const variants = {
    neutral: 'bg-gray-100 text-gray-800',
    primary: 'bg-blue-100 text-blue-800',
    info: 'bg-indigo-100 text-indigo-800',
    success: 'bg-emerald-100 text-emerald-800',
    warning: 'bg-amber-100 text-amber-800',
    danger: 'bg-red-100 text-red-800',
    purple: 'bg-purple-100 text-purple-800',
    orange: 'bg-orange-100 text-orange-800',
  };

  const currentVariant = variants[variant] || variants.neutral;

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${currentVariant}`}>
      {children}
    </span>
  );
};
