/**
 * snake_case <-> camelCase key conversion at the API boundary.
 * Only lowercase identifier keys are converted; UPPERCASE enum keys
 * (e.g. WALKER_ASSISTANCE in surcharge maps) are left untouched.
 */

const SNAKE_KEY = /^[a-z][a-z0-9]*(_[a-z0-9]+)+$/;
const CAMEL_KEY = /^[a-z][a-z0-9]*[A-Z][A-Za-z0-9]*$/;

export const snakeToCamel = (key: string): string =>
  SNAKE_KEY.test(key) ? key.replace(/_([a-z0-9])/g, (_, c: string) => c.toUpperCase()) : key;

export const camelToSnake = (key: string): string =>
  CAMEL_KEY.test(key) ? key.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`) : key;

function mapKeys(value: unknown, fn: (k: string) => string): unknown {
  if (Array.isArray(value)) return value.map((v) => mapKeys(v, fn));
  if (value !== null && typeof value === 'object' && Object.getPrototypeOf(value) === Object.prototype) {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) out[fn(k)] = mapKeys(v, fn);
    return out;
  }
  return value;
}

export const camelizeKeys = <T>(value: unknown): T => mapKeys(value, snakeToCamel) as T;
export const snakeizeKeys = (value: unknown): unknown => mapKeys(value, camelToSnake);
