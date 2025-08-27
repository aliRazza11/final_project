import { useCallback, useRef } from "react";
import { clamp } from "../utils/image";

export default function useDiffusionStream({ api }) {
  const wsRef = useRef(null);

  const closeWsIfOpen = useCallback(() => {
    try {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: "cancel" }));
        wsRef.current.close();
      }
    } catch {}
  }, []);

  const fastDiffuse = useCallback(async ({
    uploadedImageDataUrl, diffusion,
    setDiffusedImage, setCurrentStep
  }) => {
    const steps = clamp(Number(diffusion.steps) || 1, 1, 1000);
    const payload = {
      image_b64: uploadedImageDataUrl,
      steps,
      schedule: diffusion.schedule,
      beta_start: diffusion.betaMin ? Number(diffusion.betaMin) : undefined,
      beta_end: diffusion.betaMax ? Number(diffusion.betaMax) : undefined,
      seed: 42,
      return_data_url: true,
    };
    const data = await api.diffuse(payload);
    setDiffusedImage(data.image);
    setCurrentStep(steps - 1);
  }, [api]);

  const slowDiffuse = useCallback(({
    uploadedImageDataUrl, diffusion, imageId,
    onStart, onFrame, onProgress, onDone, onError,
    tOffset, saveFramesForImage
  }) => {
    closeWsIfOpen();

    const steps = clamp(Number(diffusion.steps) || 1, 1, 1000);
    const BASE_HTTP = api.baseURL || "http://localhost:8000";
    const WS_URL = BASE_HTTP.replace(/^http/, "ws") + "/diffuse/ws";
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    let collectedFrames = [];

    ws.onopen = () => {
      const previewEvery = Math.max(1, Math.floor(steps / 25));
      ws.send(JSON.stringify({
        image_b64: uploadedImageDataUrl,
        steps,
        beta_start: diffusion.betaMin ? Number(diffusion.betaMin) : 1e-3,
        beta_end: diffusion.betaMax ? Number(diffusion.betaMax) : 2e-2,
        schedule: diffusion.schedule,
        seed: 42,
        preview_every: previewEvery,
        quality: 85,
        data_url: true,
        include_metrics: true,
      }));
      onStart?.();
    };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (typeof msg.t === "number") {
          const globalT = msg.t + (tOffset || 0);
          const frame = {
            localT: msg.t,
            globalT,
            image: msg.image || null,
            metrics: msg.metrics || null,
            betas: msg.beta,
          };
          collectedFrames.push(frame);
          onFrame?.(frame);
          if (typeof msg.progress === "number")
            onProgress?.(msg.progress, msg.t);
        }
        if (msg.status === "done") {
          // Persist all frames once the run completes
          if (imageId && saveFramesForImage) {
            saveFramesForImage(imageId, collectedFrames);
          }
          onDone?.();
          ws.close();
        }
      } catch (e) {
        onError?.(e);
      }
    };

    ws.onerror = () => onError?.(new Error("WebSocket error"));
    ws.onclose = () => {};
  }, [api, closeWsIfOpen]);

  const cancel = useCallback(() => { closeWsIfOpen(); }, [closeWsIfOpen]);

  return { fastDiffuse, slowDiffuse, cancel, wsRef };
}
