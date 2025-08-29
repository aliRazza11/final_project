import { useCallback, useMemo, useRef, useState } from "react";
import useDiffusionStream from "../hooks/useDiffusionStream";
import { clamp } from "../utils/image";

export default function useDiffusionOrchestrator({
  api,
  uploadedImageDataUrl,
  currentImageKey,          
  frames,
  setFrames,
  saveFramesForImage,      
  tOffsetRef,
}) {
  // Diffusion config + view
  const [diffusedImage, setDiffusedImage] = useState(null);
  const [diffusion, setDiffusion] = useState({
    steps: 500,
    betaMin: "",
    betaMax: "",
    schedule: "linear",
  });
  const [mode, setMode] = useState("slow");


  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [streamError, setStreamError] = useState("");
  const [followStream, setFollowStream] = useState(true);


  const { fastDiffuse, slowDiffuse, cancel: cancelStream, wsRef } = useDiffusionStream({ api });

  const totalSteps = useMemo(
    () => clamp(Number(diffusion.steps) || 1, 1, 1000),
    [diffusion.steps]
  );
  const canDiffuse = Boolean(uploadedImageDataUrl);

  const resetTimelineForActiveImage = useCallback(async () => {
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: "cancel" }));
        wsRef.current.close();
      }
    } catch {}
    setFrames([]);
    setCurrentStep(0);
    setDiffusedImage(null);
    tOffsetRef.current = 0;
    setFollowStream(true);
  }, [currentImageKey, , setFrames, tOffsetRef, wsRef]);

  const diffuse = useCallback(async () => {
    if (!canDiffuse) {
      setStreamError("Please upload an image first.");
      return;
    }

    if (mode === "fast") {
      setStreamError("");
      setIsStreaming(false);
      setFollowStream(true);
      await fastDiffuse({
        uploadedImageDataUrl,
        diffusion,
        setDiffusedImage,
        setCurrentStep,
      });
      return;
    }


    await resetTimelineForActiveImage();

    setStreamError("");
    setIsStreaming(true);
    setFollowStream(true);

    const nextOffset = 0;
    tOffsetRef.current = nextOffset;

    slowDiffuse({
      uploadedImageDataUrl,
      diffusion,
      imageId: currentImageKey,     
      tOffset: nextOffset,
      saveFramesForImage,          
      onStart: () => {},
      onFrame: async (frame) => {
        if (!frame.image) return;

        setFrames((prev) => {
          const idx = prev.findIndex((f) => f.globalT === frame.globalT);
          const next =
            idx >= 0
              ? prev.map((p, i) => (i === idx ? frame : p))
              : [...prev, frame].sort((a, b) => a.globalT - b.globalT);
          return next;
        });

        if (followStream && frame.image) {
          setDiffusedImage(frame.image);
        }
      },
      onProgress: (p, t) => setCurrentStep(t),
      onDone: () => setIsStreaming(false),
      onError: (err) => {
        setIsStreaming(false);
        setStreamError(err?.message || "WebSocket error");
      },
    });
  }, [
    canDiffuse,
    mode,
    fastDiffuse,
    slowDiffuse,
    uploadedImageDataUrl,
    diffusion,
    resetTimelineForActiveImage,
    setFrames,
    currentImageKey,
    saveFramesForImage,
    followStream,
    tOffsetRef,
  ]);

  return {

    diffusion,
    setDiffusion,
    mode,
    setMode,
    isStreaming,
    currentStep,
    totalSteps,
    streamError,
    setStreamError,
    followStream,
    setFollowStream,
    diffusedImage,
    setDiffusedImage,


    diffuse,
    cancelStream,

    wsRef,
  };
}
