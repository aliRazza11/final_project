import React, { useState } from "react";
import { api } from "../../services/api";

export default function ChangeEmailModal({ onClose }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await api.updateSettings({ email, old_password: password });
      setMessage("✅ " + data.message);
    } catch (err) {
      setMessage("❌ " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow p-6 w-full max-w-sm">
        <h2 className="text-xl font-bold mb-4">Change Email</h2>
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">New Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Current Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gray-900 text-white px-4 py-2 rounded-lg"
          >
            {loading ? "Saving..." : "Save"}
          </button>
        </form>
        {message && <p className="mt-3 text-sm">{message}</p>}
        <button onClick={onClose} className="mt-4 w-full border rounded px-4 py-2">
          Close
        </button>
      </div>
    </div>
  );
}
