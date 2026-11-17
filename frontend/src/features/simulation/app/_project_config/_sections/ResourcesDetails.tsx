import type { Project } from "../../../contracts/generated";
export function ResourcesDetails({ resources, update_field }: {
  resources: Project["resources"]; update_field: (path: string[], value: unknown) => void;
}) {
  return <div className="grid grid-cols-2 gap-4 p-6">{Object.entries(resources ?? {}).map(([field, value]) =>
    <label key={field} className="flex flex-col gap-2 text-sm">{field}
      <input aria-label={field} type="number" step="any" value={value}
        onChange={(event) => update_field(["resources", field], event.target.valueAsNumber)}
        className="rounded bg-white/20 px-3 py-2" />
    </label>)}</div>;
}
