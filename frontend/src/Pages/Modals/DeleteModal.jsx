import React, { useState } from "react";
import { api } from "../../services/api";

export default function DeleteAccountModal({ onClose }) {
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleDelete = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await api.deleteAccount({ password });
      alert("✅ " + data.message);
      window.location.href = "/signup"; // redirect after deletion
    } catch (err) {
      setMessage("❌ " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow p-6 w-full max-w-sm">
        <h2 className="text-xl font-bold mb-4 text-red-600">Delete Account</h2>
        <form onSubmit={handleDelete} className="space-y-4">
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
            className="w-full bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
          >
            {loading ? "Deleting..." : "Delete Account"}
          </button>
        </form>
        {message && <p className="mt-3 text-sm">{message}</p>}
        <button onClick={onClose} className="mt-4 w-full border rounded px-4 py-2">
          Cancel
        </button>
      </div>
    </div>
  );
}
