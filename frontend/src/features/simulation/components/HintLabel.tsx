interface HintLabelProps {
  label: string;
  hint: string;
  className?: string;
}

export default function HintLabel({ label, hint, className }: HintLabelProps) {
  return (
    <div className={`relative group w-fit ${className || ""}`}>
      <label className="block mb-1 text-sm cursor-help">{label}</label>
      <div className="absolute bottom-full left-0 mb-1 hidden group-hover:block bg-black text-white text-xs px-2 py-2 rounded-md whitespace-nowrap z-10 border">
        {hint}
        <div className="absolute top-full left-2 w-2 h-2 bg-black rotate-45 transform origin-top-left"></div>
      </div>
    </div>
  );
}
