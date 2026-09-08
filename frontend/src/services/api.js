/**
 * services/api.js — all fetch calls to the FastAPI backend.
 *
 * The backend may be sleeping on a free hosting tier. Before starting a
 * review, wake it with a health request and wait until it becomes ready.
 */

const BASE_URL = import.meta.env.VITE_API_URL || "";
const HEALTH_CHECK_INTERVAL_MS = 2000;
const HEALTH_CHECK_TIMEOUT_MS = 120000;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Wait for the backend to become available.
 *
 * A request to /health is enough to wake a sleeping backend on platforms
 * such as Render. We poll for up to two minutes so cold starts don't look
 * like application errors to the user.
 */
export async function waitForBackend(onStatus) {
  const startedAt = Date.now();

  onStatus?.("Waking backend...");

  while (Date.now() - startedAt < HEALTH_CHECK_TIMEOUT_MS) {
    try {
      const response = await fetch(`${BASE_URL}/health`, {
        method: "GET",
        cache: "no-store",
      });

      if (response.ok) {
        const data = await response.json().catch(() => null);
        if (data?.status === "ok") {
          onStatus?.("Backend ready");
          return;
        }
      }
    } catch (_) {
      // Backend is still waking up or temporarily unreachable.
    }

    await sleep(HEALTH_CHECK_INTERVAL_MS);
  }

  throw new Error("Backend is taking too long to start. Please try again.");
}

/**
 * Send a PR URL to the backend and receive the full review.
 *
 * @param {string} prUrl - The GitHub PR URL the user typed in
 * @param {function} onStatus - Optional progress callback for the UI
 * @returns {Promise<object>} - The AnalyzeResponse JSON from the backend
 */
export async function analyzePR(prUrl, onStatus) {
  // Wake a sleeping backend before sending the expensive review request.
  await waitForBackend(onStatus);
  onStatus?.("Analyzing pull request...");

  const response = await fetch(`${BASE_URL}/api/review/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pr_url: prUrl }),
  });

  if (!response.ok) {
    let detail = `Server error (${response.status})`;
    try {
      const errorBody = await response.json();
      detail = errorBody.detail || detail;
    } catch (_) {
      /* ignore parse error */
    }
    throw new Error(detail);
  }

  return response.json();
}
