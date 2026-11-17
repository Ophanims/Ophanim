const ProcessBar = ({ progress, name }: { progress: number, name: string }) => {
    const percentage = progress * 100

    const get_bar_color = (p?: number) => {
      if (p === undefined || Number.isNaN(p)) return "bg-gray-400"
      if (p >= 0.9) return "bg-green-600"
      if (p >= 0.6) return "bg-lime-500"
      if (p >= 0.3) return "bg-yellow-400"
      return "bg-red-600"
    }

    const bar_color_class = get_bar_color(progress)

  return (
    <div className="mb-1">
      <div className="flex justify-between">
        <span className="text-xs text-white/50">{name}</span>
        <span className="text-xs text-white/50">
          {percentage.toFixed(2)}%
        </span>
      </div>
      <div className="w-full bg-white/20 rounded-full h-1">
        <div
          className={`${bar_color_class} h-1 rounded-full transition-all duration-500`}
          style={{ width: `${Math.abs(percentage)}%` }}
        ></div>
      </div>
    </div>
  );
};

export default ProcessBar;
