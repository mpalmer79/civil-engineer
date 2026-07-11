import type { ApiResult } from "@/lib/api/client";

// Unwraps a successful ApiResult in tests, failing loudly when the call did
// not succeed so assertions read the mapped data directly.
export function unwrap<T>(result: ApiResult<T>): T {
  if (!result.ok) {
    throw new Error(`Expected success, got ${result.kind}: ${result.message}`);
  }
  return result.data;
}

// Asserts a failure and returns it for kind/status assertions.
export function unwrapFailure<T>(result: ApiResult<T>) {
  if (result.ok) {
    throw new Error("Expected failure, got success");
  }
  return result;
}

// Wraps fixture data as a successful ApiResult for mocked getters.
export function ok<T>(data: T) {
  return { ok: true as const, data, source: "backend" as const, status: 200 };
}
