import React, { useState } from "react";

/**
 * PRInputForm — the search bar of the app.
 *
 * Controlled input: React owns the value via state.
 * We do basic client-side validation (non-empty, looks like a GitHub URL)
 * before calling the parent's onSubmit — this saves a round-trip for
 * obviously invalid input.
 */
export default function PRInputForm({ onSubmit, isLoading }) {
  const [url, setUrl] = useState("");
  const [localError, setLocalError] = useState("");

  function validate(value) {
    if (!value.trim()) return "Please enter a GitHub PR URL.";
    if (!value.includes("github.com") || !value.includes("/pull/")) {
      return 'URL must look like: https://github.com/owner/repo/pull/123';
    }
    return null;
  }

  function handleSubmit(e) {
    e.preventDefault();
    const err = validate(url);
    if (err) {
      setLocalError(err);
      return;
    }
    setLocalError("");
    onSubmit(url.trim());
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          {/* GitHub icon */}
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 .5C5.73.5.5 5.73.5 12c0 5.08 3.29 9.39 7.86 10.91.57.1.78-.25.78-.55v-1.93c-3.19.69-3.86-1.54-3.86-1.54-.52-1.33-1.27-1.68-1.27-1.68-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.02 1.75 2.68 1.24 3.33.95.1-.74.4-1.24.72-1.53-2.55-.29-5.23-1.27-5.23-5.67 0-1.25.45-2.28 1.18-3.08-.12-.29-.51-1.46.11-3.04 0 0 .96-.31 3.15 1.18a10.96 10.96 0 0 1 5.74 0c2.19-1.49 3.15-1.18 3.15-1.18.62 1.58.23 2.75.11 3.04.74.8 1.18 1.83 1.18 3.08 0 4.41-2.69 5.38-5.25 5.66.41.35.78 1.05.78 2.12v3.14c0 .3.21.66.79.55C20.21 21.39 23.5 17.08 23.5 12 23.5 5.73 18.27.5 12 .5z"/>
            </svg>
          </span>
          <input
            id="pr-url-input"
            type="url"
            value={url}
            onChange={(e) => { setUrl(e.target.value); setLocalError(""); }}
            placeholder="https://github.com/owner/repo/pull/123"
            disabled={isLoading}
            className="w-full bg-gray-900 border border-gray-700 rounded-xl pl-11 pr-4 py-3.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition disabled:opacity-50"
            autoComplete="off"
            spellCheck="false"
          />
        </div>
        <button
          id="analyze-btn"
          type="submit"
          disabled={isLoading}
          className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-semibold px-7 py-3.5 rounded-xl text-sm transition-all duration-200 shadow-lg shadow-violet-900/30 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {isLoading ? "Analyzing…" : "Analyze PR"}
        </button>
      </div>

      {localError && (
        <p className="text-red-400 text-sm pl-1">{localError}</p>
      )}
    </form>
  );
}
