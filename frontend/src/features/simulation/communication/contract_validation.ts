import bundle from "../contracts/schema.json";

type Schema = { $ref?: string; anyOf?: Schema[]; const?: unknown; enum?: unknown[];
  type?: string; required?: string[]; properties?: Record<string, Schema>;
  additionalProperties?: boolean | Schema; items?: Schema | boolean; prefixItems?: Schema[];
  minimum?: number; maximum?: number; exclusiveMinimum?: number; minLength?: number;
  maxLength?: number; minItems?: number; maxItems?: number };
const definitions: Record<string, Schema> = bundle.$defs;

function validate_value(value: unknown, schema: Schema, path: string): void {
  if (schema.$ref) return validate_value(value, definitions[schema.$ref.split("/").pop()!], path);
  if (schema.anyOf) {
    for (const candidate of schema.anyOf) {
      try { validate_value(value, candidate, path); return; } catch { /* Try the next declared union member. */ }
    }
    throw new Error(`${path}: invalid union value`);
  }
  if ("const" in schema && value !== schema.const) throw new Error(`${path}: unexpected constant`);
  if (schema.enum && !schema.enum.includes(value)) throw new Error(`${path}: unexpected enum value`);
  if (schema.type === "null" && value !== null) throw new Error(`${path}: expected null`);
  if (schema.type === "string") {
    if (typeof value !== "string") throw new Error(`${path}: expected string`);
    if (schema.minLength !== undefined && value.length < schema.minLength) throw new Error(`${path}: too short`);
    if (schema.maxLength !== undefined && value.length > schema.maxLength) throw new Error(`${path}: too long`);
  }
  if (schema.type === "number" || schema.type === "integer") {
    if (typeof value !== "number" || !Number.isFinite(value) || (schema.type === "integer" && !Number.isInteger(value))) throw new Error(`${path}: expected finite ${schema.type}`);
    if (schema.minimum !== undefined && value < schema.minimum) throw new Error(`${path}: below minimum`);
    if (schema.maximum !== undefined && value > schema.maximum) throw new Error(`${path}: above maximum`);
    if (schema.exclusiveMinimum !== undefined && value <= schema.exclusiveMinimum) throw new Error(`${path}: must exceed minimum`);
  }
  if (schema.type === "boolean" && typeof value !== "boolean") throw new Error(`${path}: expected boolean`);
  if (schema.type === "array") {
    if (!Array.isArray(value)) throw new Error(`${path}: expected array`);
    if (schema.minItems !== undefined && value.length < schema.minItems) throw new Error(`${path}: too few items`);
    if (schema.maxItems !== undefined && value.length > schema.maxItems) throw new Error(`${path}: too many items`);
    value.forEach((item, index) => {
      const child = schema.prefixItems?.[index] ?? schema.items;
      if (child === false) throw new Error(`${path}: unexpected item`);
      if (child && child !== true) validate_value(item, child, `${path}[${index}]`);
    });
  }
  if (schema.type === "object") {
    if (value === null || typeof value !== "object" || Array.isArray(value)) throw new Error(`${path}: expected object`);
    const object = value as Record<string, unknown>;
    for (const name of schema.required ?? []) if (!(name in object)) throw new Error(`${path}.${name}: required`);
    for (const [name, item] of Object.entries(object)) {
      const child = schema.properties?.[name];
      if (child) validate_value(item, child, `${path}.${name}`);
      else if (schema.additionalProperties === false) throw new Error(`${path}.${name}: unexpected field`);
      else if (typeof schema.additionalProperties === "object") validate_value(item, schema.additionalProperties, `${path}.${name}`);
    }
  }
}

export function validate_contract<T>(value: unknown, name: string): T {
  if (!definitions[name]) throw new Error(`Unknown contract: ${name}`);
  validate_value(value, definitions[name], name);
  return value as T; // The runtime schema above validates the boundary before the type assertion.
}
