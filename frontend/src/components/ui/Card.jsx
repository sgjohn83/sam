export const Card = ({ children, header, footer, className }) => (
  <div className={`bg-white shadow rounded-lg border ${className}`}>
    {header && <div className="p-4 border-b font-semibold">{header}</div>}
    <div className="p-4">{children}</div>
    {footer && <div className="p-4 border-t bg-gray-50">{footer}</div>}
  </div>
);
