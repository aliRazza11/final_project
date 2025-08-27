export async function forceDownload(url, filename) {
  try {
    const res = await fetch(url, { credentials: "include" });
    if (!res.ok) throw new Error("Failed to download file");

    const blob = await res.blob();
    const objectUrl = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = objectUrl;
    a.download = filename || "download";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    window.URL.revokeObjectURL(objectUrl);
  } catch (err) {
    console.error("Download failed:", err);
  }
}
