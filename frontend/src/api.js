const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function searchByImage(file, { category, limit } = {}) {
  const form = new FormData();
  form.append("image", file);
  if (category) {
    form.append("category", category);
  }
  if (limit) {
    form.append("limit", String(limit));
  }

  const response = await fetch(`${API_BASE_URL}/search`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Search failed");
  }

  return response.json();
}
