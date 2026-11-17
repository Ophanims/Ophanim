"use client";
// 

// import { SatelliteConfig } from "../../../types";

// interface SatDetailsProps {
//   satellites: SatelliteConfig[];
// }

// export const SatDetails = ({ satellites }: SatDetailsProps) => {
//   const sats = satellites ?? [];
//   return (
//     <div className="text-sm">
//       <div className="flex py-2 items-center gap-3">
//         <div className="flex w-1/3">
//           <div className="flex w-2/3">
//             <div className="w-1/2 px-2 text-white">ID</div>
//             <div className="w-1/2 px-2 text-white">Serial</div>
//           </div>
//           <div className="flex w-1/3">
//             <div className="w-1/2 px-2 text-white">Plane</div>
//             <div className="w-1/2 px-2 text-white">Order</div>
//           </div>
//         </div>
//         <div className="flex w-2/3">
//           <div className="w-1/2 px-2 text-white">TLE 1</div>
//           <div className="w-1/2 px-2 text-white">TLE 2</div>
//         </div>
//       </div>
//       {sats.length === 0 && (
//         <p className="text-gray-400 italic text-sm mb-2">No satellites</p>
//       )}
//       {sats.map((sat, i) => (
//         <div
//           key={i}
//           className="flex items-center py-1 gap-3 border-b border-white/20"
//         >
//           <div className="flex w-1/3">
//             <div className="flex w-2/3">
//               <div className="w-1/2 px-2 text-white">
//                 {sat.id ? sat.id.slice(-12) : "Pending"}
//               </div>
//               <div className="w-1/2 px-2 text-white">{sat.name}</div>
//             </div>
//             <div className="flex w-1/3">
//               <div className="w-1/2 px-2 text-white">{sat.plane}</div>
//               <div className="w-1/2 px-2 text-white">{sat.order}</div>
//             </div>
//           </div>
//           <div className="flex w-2/3">
//             <div className="w-1/2 px-2 text-white">{sat.tle1}</div>
//             <div className="w-1/2 px-2 text-white">{sat.tle2}</div>
//           </div>
//         </div>
//       ))}
//     </div>
//   );
// };
