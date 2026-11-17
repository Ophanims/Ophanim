import React,{ useEffect,useState } from "react";

interface StepProgressBarProps {
  step: number; // 1-based: 当前步骤（高亮到哪一步，包括当前）
  steps: {
    name: string;
    icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  }[]; // icon为Heroicon组件
}

const StepProgressBar: React.FC<StepProgressBarProps> = ({ step, steps }) => {
  const len = step < steps.length - 1 ? steps.length - 1 : steps.length;
  const [blink, set_blink] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => set_blink((b) => !b), 1000); // 每秒变色
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center">
      {Array.from({ length: len }, (_, idx) => {
        const Icon = steps[idx].icon;
        return (
          <React.Fragment key={idx}>
            {/* 圆圈和图标 */}
            <div
              className={`
                relative z-10 w-8 h-8 flex flex-col items-center justify-center rounded-full 
                text-lg border-2 transition-colors duration-500
                ${
                  idx === step
                    ? blink
                      ? "border-yellow-600 text-yellow-600"
                      : "border-white/30 text-white/30"
                    : idx < step
                    ? "border-yellow-600 text-yellow-600"
                    : "border-white/30 text-white/30"
                }
              `}
            >
              <span>{Icon && <Icon className="w-4 h-4" />}</span>
            </div>
            {/* 横线（除最后一个step外） */}
            {idx < len - 1 && (
              <div
                className={`flex-1 w-0.5 mx-1 min-h-4 transition-colors duration-500
                  ${
                    idx === step - 1
                      ? blink
                        ? "bg-yellow-600"
                        : "bg-white/30"
                      : idx < step
                      ? "bg-yellow-600"
                      : "bg-white/30"
                  }
                `}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

export default StepProgressBar;
