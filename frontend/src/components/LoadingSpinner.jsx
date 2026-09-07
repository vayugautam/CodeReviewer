import React from "react";

/**
 * LoadingSpinner — shown while the backend fetches GitHub data and runs the LLM.
 * Displays estimated wait time to set user expectations.
 */
export default function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center gap-4 py-16 text-center">
      {/* Animated ring */}
      <div className="w-12 h-12 rounded-full border-4 border-gray-800 border-t-violet-500 animate-spin" />
      <div className="space-y-1">
        <p className="text-gray-300 font-medium text-sm">Analyzing pull request…</p>
        <p className="text-gray-600 text-xs">
          Fetching diff · Running static checks · Asking Gemini AI
        </p>
        <p className="text-gray-700 text-xs mt-2">This usually takes 5–15 seconds</p>
      </div>
    </div>
  );
}
