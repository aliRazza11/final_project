// src/hooks/useImageSwitch.js
import { useCallback } from "react";

/**
 * Handles switching the active image, canceling any running WS stream,
 * persisting/restoring per-image timelines, and restoring preview.
 */
export default function useImageSwitch({
  wsRef,
  setStreamError,
  currentImageKey,
  setCurrentImageKey,
  setUploadedImage,
  setUploadedImageDataUrl,
  saveFramesForImage,
  loadFramesForImage,
  setFrames,
  setScrubT,
  computeNextOffsetFrom,
  tOffsetRef,
  setDiffusedImage,
  setAnalysisAvailable,
  setFollowStream,
  frames,
}) {
  const switchToImage = useCallback(
    async (key, imageUrl, dataUrl) => {
      // stop any running stream
      try {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ action: "cancel" }));
          wsRef.current.close();
        }
      } catch {}

      setStreamError("");

      // persist current image's frames
      if (currentImageKey) await saveFramesForImage(currentImageKey, frames);

      // set active image
      setCurrentImageKey(key || null);
      setUploadedImage(imageUrl || null);
      setUploadedImageDataUrl(dataUrl || null);

      // restore timeline
      const restored = key ? await loadFramesForImage(key) : [];
      setFrames(restored);
      setScrubT(null);
      tOffsetRef.current = computeNextOffsetFrom(restored);

      // restore preview from last frame
      if (restored.length) {
        const last = restored[restored.length - 1];
        if (last?.image) setDiffusedImage(last.image);
      } else {
        setDiffusedImage(null);
      }

      setAnalysisAvailable(restored.length > 0);
      setFollowStream(true);
    },
    [
      wsRef,
      setStreamError,
      currentImageKey,
      saveFramesForImage,
      frames,
      setCurrentImageKey,
      setUploadedImage,
      setUploadedImageDataUrl,
      loadFramesForImage,
      setFrames,
      setScrubT,
      computeNextOffsetFrom,
      tOffsetRef,
      setDiffusedImage,
      setAnalysisAvailable,
      setFollowStream,
    ]
  );

  return { switchToImage };
}
