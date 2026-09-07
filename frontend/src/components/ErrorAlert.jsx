import React from "react";

/**
 * ErrorAlert — displays backend or network errors clearly.
 */
export default function ErrorAlert({ message }) {
  return (
    <div className="rounded-xl border border-red-800 bg-red-950/50 p-5 flex gap-3 items-start">
      <span className="text-red-400 text-xl mt-0.5">⚠</span>
      <div>
        <p className="font-semibold text-red-300 text-sm">Analysis failed</p>
        <p className="text-red-400/80 text-sm mt-1">{message}</p>
      </div>
    </div>
  );
}
