export async function request(path: string, options?: RequestInit) {
  const r = await fetch("/api/" + path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!r.ok) {
    const b = await r.json().catch(() => ({}));
    throw new Error(
      typeof b.detail === "string"
        ? b.detail
        : "Le service est momentanément indisponible.",
    );
  }
  const method = (options?.method || "GET").toUpperCase();
  if (method !== "GET" && path.startsWith("admin/") && !path.endsWith("/preview") && path !== "admin/data-structure/process") {
    invalidateLibraryCache();
  }
  return r.status === 204 ? null : r.json();
}

// Public library pages only: no admin responses, exercises or learner progress.
const libraryCache = new Map<string, {value: unknown; expires: number}>();
const libraryPending = new Map<string, Promise<unknown>>();
const LIBRARY_TTL = 5 * 60 * 1000;
const LIBRARY_LIMIT = 120;
let libraryGeneration = 0;
export const libraryVersion = () => libraryGeneration;
export function invalidateLibraryCache() {
  libraryGeneration += 1;
  libraryCache.clear();
  libraryPending.clear();
  if (typeof window !== "undefined") window.dispatchEvent(new Event("library-data-changed"));
}
export function peekLibrary<T>(path: string): T | undefined {
  const entry = libraryCache.get(path);
  if (!entry) return undefined;
  if (entry.expires <= Date.now()) { libraryCache.delete(path); return undefined; }
  libraryCache.delete(path); libraryCache.set(path, entry);
  return entry.value as T;
}
export function cachedLibrary<T>(path: string): Promise<T> {
  if (!/^(topics(?:$|\/)|words\/[^/]+\/phrases(?:\?|$)|library\?kind=letter(?:&|$))/.test(path)) {
    return Promise.reject(new Error("Ce cache est réservé à la bibliothèque publique."));
  }
  const cached = peekLibrary<T>(path);
  if (cached !== undefined) return Promise.resolve(cached);
  const pending = libraryPending.get(path);
  if (pending) return pending as Promise<T>;
  const generation = libraryGeneration;
  const task = request(path).then((value: T) => {
    if (generation === libraryGeneration) {
      libraryCache.set(path, {value, expires: Date.now() + LIBRARY_TTL});
      while (libraryCache.size > LIBRARY_LIMIT) libraryCache.delete(libraryCache.keys().next().value!);
    }
    return value;
  }).finally(() => {
    if (libraryPending.get(path) === task) libraryPending.delete(path);
  });
  libraryPending.set(path, task);
  return task;
}
