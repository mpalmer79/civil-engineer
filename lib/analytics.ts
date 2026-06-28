// Lightweight, client-side demo analytics helper.
//
// This is intentionally a local no-op abstraction. It does not load any
// third-party analytics package, does not send any data to an external service,
// and does not capture personal data or submission content. In development it
// logs the event name and a small set of non-sensitive properties to the console
// so the event flow can be inspected; in production it is a no-op until a real
// analytics sink is wired in.
//
// Future work: route trackDemoEvent through a real analytics provider (or a
// first-party endpoint) behind an explicit opt-in. The event names below are the
// stable contract a future sink can consume.

export type DemoAnalyticsEvent =
  | "demo_started"
  | "demo_step_viewed"
  | "demo_completed"
  | "demo_cta_clicked"
  | "pilot_cta_clicked";

// Only non-sensitive, demo-shape properties are ever passed (step index, step
// id, CTA label, sample project id). No user data, no file content, no secrets.
export type DemoAnalyticsProps = Record<string, string | number | boolean>;

export function trackDemoEvent(
  event: DemoAnalyticsEvent,
  props: DemoAnalyticsProps = {},
): void {
  // Guard for non-browser (server render) contexts.
  if (typeof window === "undefined") return;
  if (process.env.NODE_ENV !== "production") {
    // eslint-disable-next-line no-console
    console.debug("[demo-analytics]", event, props);
  }
  // No external network call. A real sink can be attached here later.
}
