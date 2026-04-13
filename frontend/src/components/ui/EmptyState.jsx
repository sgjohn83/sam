export const EmptyState = ({ message, icon: Icon }) => (
  <div className="flex flex-col items-center justify-center p-8 text-center text-gray-500">
    {Icon && <Icon className="w-12 h-12 mb-2 text-gray-400" />}
    <p>{message}</p>
  </div>
);
