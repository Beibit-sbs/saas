import { ApiRequestError } from "@/shared/api/client";

export interface NormalizedError {
  code: string;
  message: string;
  actionable: string;
}

/**
 * Normalises any thrown value (ApiRequestError, generic Error, unknown) into
 * a consistent shape safe for display in toasts and error states.
 */
export function normalizeApiError(err: unknown): NormalizedError {
  if (err instanceof ApiRequestError) {
    switch (err.status) {
      case 401:
        return {
          code: "UNAUTHORIZED",
          message: "Your session has expired.",
          actionable: "Please log in again.",
        };
      case 403:
        return {
          code: "FORBIDDEN",
          message: "You don't have permission to perform this action.",
          actionable: "Contact your administrator if access is required.",
        };
      case 404:
        return {
          code: "NOT_FOUND",
          message: "The requested resource was not found.",
          actionable: "Check the ID and try again.",
        };
      case 409:
        return {
          code: "CONFLICT",
          message: err.message || "A conflict occurred.",
          actionable: "Refresh the page and try again.",
        };
      case 422:
        return {
          code: "VALIDATION_ERROR",
          message: err.message || "Validation failed.",
          actionable: "Check your input and try again.",
        };
      case 503:
        return {
          code: "SERVICE_UNAVAILABLE",
          message: "The service is temporarily unavailable.",
          actionable: "Wait a moment and retry.",
        };
      default:
        return {
          code: err.code ?? `HTTP_${err.status}`,
          message: err.message || `Request failed (${err.status}).`,
          actionable: "Try again or contact support.",
        };
    }
  }

  if (err instanceof Error) {
    if (err.name === "AbortError") {
      return {
        code: "ABORTED",
        message: "Request was cancelled.",
        actionable: "",
      };
    }
    // Network errors (fetch throws TypeError when offline)
    if (err.name === "TypeError" || err.message.toLowerCase().includes("network")) {
      return {
        code: "NETWORK_ERROR",
        message: "Network error — could not reach the server.",
        actionable: "Check your connection and retry.",
      };
    }
    return {
      code: "UNKNOWN_ERROR",
      message: err.message || "An unexpected error occurred.",
      actionable: "Try again or contact support.",
    };
  }

  return {
    code: "UNKNOWN_ERROR",
    message: "An unexpected error occurred.",
    actionable: "Try again or contact support.",
  };
}

/** Formatted string suitable for a toast title. */
export function toastError(err: unknown): string {
  const { message, actionable } = normalizeApiError(err);
  return actionable ? `${message} ${actionable}` : message;
}
