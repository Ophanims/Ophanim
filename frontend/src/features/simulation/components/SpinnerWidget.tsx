interface SpinnerProps {
  className: string;
}
export const SpinnerWidget = ({ className }: SpinnerProps) => {
  return (
    <div
      className={`${className} border-t-transparent rounded-full animate-spin`}
    />
  );
};
