import LinkDataCard from "../../../components/LinkDataCard";
import type { LinkSnapshot } from "../../../contracts/generated";
import { InventorySection } from "./InventorySection";

export default function NetworkPanel({ links, has_frame, search_content }: {
  links: LinkSnapshot[]; has_frame: boolean; search_content: string;
}) {
  return <>{[["ISL", "Inter-Satellite Links"], ["UL", "Uplink"], ["DL", "Downlink"]].map(([type, title]) => {
    const matches = links.filter((link) => link.type === type && `${link.src} ${link.dst}`.toLowerCase().includes(search_content.toLowerCase()));
    return <InventorySection key={type} title={title}>
      {!matches.length && <p className="py-4 text-white/40">{has_frame ? "No matching active links." : "Start a simulation to inspect links."}</p>}
      {matches.map((link) => <LinkDataCard key={`${link.type}:${link.src}:${link.dst}`} link={link} />)}
    </InventorySection>;
  })}</>;
}
