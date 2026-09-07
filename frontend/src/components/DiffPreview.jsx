import React, { useState } from "react";

/** A deliberately plain-text view: untrusted code is never interpreted as HTML. */
export default function DiffPreview({ diff }) {
  const [open, setOpen] = useState(false);
  if (!diff) return null;

  return (
    <section className="rounded-2xl border border-gray-800 bg-gray-900/50 overflow-hidden">
      <button
        type="button"
        className="w-full px-6 py-4 flex items-center justify-between text-sm text-gray-300 hover:bg-gray-800/40"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        <span className="font-semibold">Raw diff preview</span>
        <span className="text-xs text-indigo-400">{open ? "Hide" : "Show"}</span>
      </button>
      {open && (
        <pre className="border-t border-gray-800 p-4 overflow-x-auto max-h-96 text-xs leading-relaxed text-gray-300 bg-black/20 whitespace-pre">
          {diff}
        </pre>
      )}
    </section>
  );
}
