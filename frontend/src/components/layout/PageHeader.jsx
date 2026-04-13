export const PageHeader = ({ title, actions }) => {
  return (
    <div className="flex justify-between items-center mb-6">
      <h1 className="text-2xl font-bold text-gray-800">{title}</h1>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  );
};
