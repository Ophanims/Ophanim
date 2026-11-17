import React,{ useState } from "react";

// 通用抖动Icon容器
export function ShakingIcon({
  className = "",
  children,
  onClick,
}: {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}) {
  const [rotated, set_rotated] = useState(false);

  const shake = () => {
    let shake_count = 0;
    const do_shake = () => {
      set_rotated(true);
      setTimeout(() => {
        set_rotated(false);
        shake_count++;
        if (shake_count < 2) {
          setTimeout(do_shake, 150);
        }
      }, 150);
    };
    do_shake();
  };

  return (
    <div className={className} onMouseEnter={shake}>
      <div
        className={`transition-transform duration-150 ${
          rotated ? "rotate-[25deg]" : ""
        }`}
        style={rotated ? { transform: "rotate(25deg)" } : {}}
        onClick={onClick}
      >
        {children}
      </div>
    </div>
  );
}
