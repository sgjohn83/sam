import { clsx } from 'clsx';

export const Button = ({ variant = 'primary', size = 'md', loading, children, className, ...props }) => {
  const variants = {
    primary: 'bg-primary text-white hover:bg-blue-600',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
    danger: 'bg-danger text-white hover:bg-red-700',
    ghost: 'bg-transparent text-gray-600 hover:bg-gray-100',
  };
  const sizes = { sm: 'px-3 py-1.5 text-sm', md: 'px-4 py-2', lg: 'px-6 py-3 text-lg' };
  
  return (
    <button 
      className={clsx('rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center', variants[variant], sizes[size], className)}
      disabled={loading}
      {...props}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
};
