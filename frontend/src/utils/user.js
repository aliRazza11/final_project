import { api } from "../services/api";

export async function getCurrentUsername() {
  try {
    const data = await api.me();
    return data.username;
  } catch (err) {
    console.error("Failed to fetch user:", err);
    return null;
  }
}
