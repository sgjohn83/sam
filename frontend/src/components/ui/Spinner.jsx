export const Spinner = ({ fullPage }) => {
  const spinner = <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>;
  if (fullPage) return <div className="flex h-screen w-full items-center justify-center">{spinner}</div>;
  return spinner;
};
