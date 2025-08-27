import React from "react";

export default function NoticeModal({ open, title = "Notice", message, onClose }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Modal */}
      <div className="relative z-10 w-full max-w-sm rounded-2xl bg-white shadow-xl border p-5">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <p className="mt-2 text-sm text-gray-600">{message}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-gray-900 text-white text-sm hover:bg-black"
          >
            OK
          </button>
        </div>
      </div>
    </div>
  );
}
