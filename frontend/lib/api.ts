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
  return r.status === 204 ? null : r.json();
}
