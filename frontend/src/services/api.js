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
};
