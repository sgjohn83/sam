import { forwardRef } from 'react';
import { clsx } from 'clsx';

export const Input = forwardRef(({ label, error, helperText, className, ...props }, ref) => (
  <div className="w-full">
    {label && <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>}
    <input 
      ref={ref}
      className={clsx('w-full rounded-lg border-gray-300 shadow-sm focus:border-primary focus:ring-primary', error && 'border-danger focus:border-danger', className)}
      {...props}
    />
    {error && <p className="text-danger text-xs mt-1">{error}</p>}
    {helperText && <p className="text-gray-500 text-xs mt-1">{helperText}</p>}
  </div>
));
