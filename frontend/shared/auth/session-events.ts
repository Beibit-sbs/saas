export const SESSION_INVALID_EVENT = "admin:session-invalid";
export const BACKEND_UNAVAILABLE_EVENT = "admin:backend-unavailable";

interface SessionInvalidDetail {
  status: number;
}

function emit(name: string, detail: object) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(name, { detail }));
}

export function emitSessionInvalid(detail: SessionInvalidDetail) {
  emit(SESSION_INVALID_EVENT, detail);
}

export function emitBackendUnavailable(detail: { status: number }) {
  emit(BACKEND_UNAVAILABLE_EVENT, detail);
}

export function onSessionInvalid(listener: (detail: SessionInvalidDetail) => void) {
  if (typeof window === "undefined") return () => {};
  const handler = (event: Event) => listener((event as CustomEvent<SessionInvalidDetail>).detail);
  window.addEventListener(SESSION_INVALID_EVENT, handler);
  return () => window.removeEventListener(SESSION_INVALID_EVENT, handler);
}