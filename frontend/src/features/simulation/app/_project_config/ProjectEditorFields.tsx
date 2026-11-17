import type { ReactNode } from "react";
import schema from "../../contracts/schema.json";
import type { Project } from "../../contracts/generated";
import { local_to_utciso_string, to_input_local } from "../../services/date_time/time_convert";
import type { ProjectFormField } from "./project_form_fields";

interface FieldSchema {
  $ref?: string;
  type?: string;
  properties?: Record<string, FieldSchema>;
  anyOf?: FieldSchema[];
  minimum?: number;
  maximum?: number;
  exclusiveMinimum?: number;
}
const definitions: Record<string, FieldSchema> = schema.$defs;
export const FIELD_STYLE = "w-full min-w-0 rounded-md border border-white/25 bg-black/20 px-3 py-2 text-sm text-white outline-none transition-colors placeholder:text-white/30 focus:border-white/80 disabled:text-white/40";

function resolve_schema(schema: FieldSchema): FieldSchema {
  if (schema.$ref) return resolve_schema(definitions[schema.$ref.split("/").pop()!]);
  return schema.anyOf ? resolve_schema(schema.anyOf.find((item) => item.type !== "null")!) : schema;
}
function get_field_schema(path: readonly string[]): FieldSchema {
  let schema = definitions.Project;
  for (const field of path) schema = resolve_schema(schema).properties![field];
  return resolve_schema(schema);
}
function read_field(project: Project, path: readonly string[]): unknown {
  let value: unknown = project;
  for (const field of path) value = value && typeof value === "object" ? (value as Record<string, unknown>)[field] : null;
  return value;
}

export function FormSection({ title, children }: { title: string; children: ReactNode }) {
  return <section className="rounded-md px-1 py-4 sm:px-4">
    <h3 className="mb-4 text-xs font-semibold tracking-widest text-white/80 uppercase">{title}</h3>
    <div className="grid gap-x-5 gap-y-4 sm:grid-cols-2">{children}</div>
  </section>;
}

export function ProjectEditorField({ field, form, update_field }: {
  field: ProjectFormField;
  form: Project;
  update_field: (path: string[], value: unknown) => void;
}) {
  const value = read_field(form, field.path);
  const definition = get_field_schema(field.path);
  const type = field.type ?? "number";
  const input_value = type === "datetime-local" && typeof value === "string" && value
    ? to_input_local(value) : typeof value === "string" || typeof value === "number" ? value : "";
  const optional = ["end_time", "time_slot"].includes(field.path[field.path.length - 1]);
  return <label className="flex min-w-0 flex-col gap-1.5 text-xs text-white/75">
    <span>{field.label}</span>
    <input name={field.path.join(".")} type={type} value={input_value} className={FIELD_STYLE}
      required={!optional} step={definition.type === "integer" ? 1 : "any"}
      min={definition.minimum ?? (definition.exclusiveMinimum === 0 ? Number.MIN_VALUE : undefined)}
      max={definition.maximum}
      onChange={(event) => {
        const input = event.target.value;
        const next = type === "number" ? (input && Number.isFinite(event.target.valueAsNumber) ? event.target.valueAsNumber : null)
          : type === "datetime-local" ? (input ? local_to_utciso_string(input) : null) : input;
        update_field([...field.path], next);
      }} />
  </label>;
}
