// src/utils/file.js

/** Base64 (no header) -> Uint8Array */
export function base64ToBytes(base64) {
  const binary = atob(base64);
  const len = binary.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

/** Base64 PNG (no data URL header) -> Blob */
export function base64ToPngBlob(base64) {
  const bytes = base64ToBytes(base64);
  return new Blob([bytes], { type: "image/png" });
}

/** Base64 PNG -> File (handy for MNIST upload) */
export function base64ToPngFile(base64, name = "image.png") {
  const blob = base64ToPngBlob(base64);
  return new File([blob], name, { type: "image/png" });
}
