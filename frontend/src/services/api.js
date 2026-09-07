/**
 * services/api.js — all fetch calls to the FastAPI backend.
 *
 * Why centralise API calls here?
 *   If the base URL or endpoint names change, we fix it in one place.
 *   Components stay clean — they just call `analyzePR(url)`, they don't
 *   know or care about HTTP details.
 */

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Send a PR URL to the backend and receive the full review.
 *
 * @param {string} prUrl  - The GitHub PR URL the user typed in
 * @returns {Promise<object>} - The AnalyzeResponse JSON from the backend
 * @throws {Error} with a human-readable message on failure
 */
export async function analyzePR(prUrl) {
  const response = await fetch(`${BASE_URL}/api/review/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pr_url: prUrl }),
  });

  if (!response.ok) {
    // Try to extract the FastAPI error detail
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
