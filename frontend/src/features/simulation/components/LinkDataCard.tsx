import { LinkSnapshot } from "@/features/simulation/types/simulation";
import React from "react";

interface LinkDataCardProps {
  link: LinkSnapshot;
}

const LinkDataCard: React.FC<LinkDataCardProps> = ({ link }) => {
  return (
    <div className="w-full rounded-lg p-2 shadow border border-white/10 mb-2">
      
      <div className="flex justify-between mb-1">
        {link.type === "ISL" ? (
         <span className="text-xs text-white/60">
          From{" "}
          <span className="text-white">
            {link.src.split("-")[1]}, {link.src.split("-")[2]}
          </span>{" "}
          To{" "}
          <span className="text-white">
            {link.dst.split("-")[1]}, {link.dst.split("-")[2]}
          </span>
        </span>
        ) : (
          <span className="text-xs text-white/60">
          From{" "}
          <span className="text-white">
            {link.src.slice(-5)}
          </span>{" "}
          To{" "}
          <span className="text-white">
            {link.dst.slice(-5)}
          </span>
        </span>
        )}
        
      </div>
      <div className="flex justify-between">
        <span className="text-xs text-white/60">Link Type:</span>
        <span
          className={`text-xs px-3 rounded-xl
      ${
        link.type === "ISL"
          ? "border border-purple-600 text-purple-600 bg-purple-800/20"
          : "border border-yellow-600 text-yellow-600 bg-yellow-800/20"
      }`}
        >
          {link.type}
        </span>
      </div>
      <div className="flex justify-between">
        <span className="text-xs text-white/60">Distance</span>
        <span className="text-xs text-white">
          {(link.distance / 1000).toFixed(2)} KM
        </span>
      </div>
      <div className="flex justify-between">
        <span className="text-xs text-white/60">SNR</span>
        <span className="text-xs text-white">{link.snr.toFixed(2)} dB</span>
      </div>
      <div className="flex justify-between">
        <span className="text-xs text-white/60">Rate</span>
        <span className="text-xs text-white">
          {link.rate >= 1e9
            ? `${(link.rate / 1e9).toFixed(2)} Gbps`
            : link.rate >= 1e6
            ? `${(link.rate / 1e6).toFixed(2)} Mbps`
            : `${link.rate.toFixed(2)} bps`}
        </span>
      </div>
    </div>
  );
};

export default LinkDataCard;
