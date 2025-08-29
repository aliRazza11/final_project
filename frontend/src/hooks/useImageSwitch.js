import { useCallback } from "react";


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
    
      try {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ action: "cancel" }));
          wsRef.current.close();
        }
      } catch {}

      setStreamError("");

 
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
