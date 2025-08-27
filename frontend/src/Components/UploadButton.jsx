import React from "react";
import { Upload } from "lucide-react";

export default function UploadButton({ onSelect, label = "Choose File", compact = false }) {
  const onChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    onSelect?.(file);
  };

  return (
    <label
      className={`bg-gray-900 text-white ${
        compact ? "px-4 py-2" : "px-6 py-3"
      } rounded-lg cursor-pointer hover:bg-gray-800 transition font-medium flex items-center gap-2`}
    >
      <Upload size={compact ? 18 : 24} className="opacity-80" />
      <span>{label}</span>
      <input type="file" accept="image/*" onChange={onChange} className="hidden" />
    </label>
  );
}
