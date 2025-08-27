// src/services/api.js
const BASE = "/api";

async function http(url, options = {}) {
  const res = await fetch(`${BASE}${url}`, { credentials: "include", ...options });
  if (!res.ok) {
    let message = "Request failed";
    try {
      const err = await res.json();
      message = err.detail || JSON.stringify(err);
    } catch {}
    throw new Error(message);
  }
  return res.json();
}

// keep your original top-level methods for backwards compatibility
export const api = {
  get: (path) => http(path),
  fetchImages: () => http("/images"),
  me: () => http("/auth/me"),

  uploadImage: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return http("/images", { method: "POST", body: fd });
  },

  deleteImage: (id) => http(`/images/${id}`, { method: "DELETE" }),

  diffuse: (payload) =>
    http("/diffuse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  logout: () => http("/auth/logout", { method: "POST" }),

  updateSettings: (payload) =>
    http("/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  deleteAccount: (payload) =>
    http("/settings/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  // ─────────────────────────────────────────────────────────────
  // Convenience namespaces (new):
  images: {
    list: () => http("/images"),
    byDigit: (d) => http(`/images/digit/${d}`),
    upload: (file) => {
      const fd = new FormData();
      fd.append("file", file);
      return http("/images", { method: "POST", body: fd });
    },
    remove: (id) => http(`/images/${id}`, { method: "DELETE" }),
  },
  auth: {
    me: () => http("/auth/me"),
    logout: () => http("/auth/logout", { method: "POST" }),
  },
  settings: {
    update: (payload) =>
      http("/settings", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),
    deleteAccount: (payload) =>
      http("/settings/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),
  },
};
