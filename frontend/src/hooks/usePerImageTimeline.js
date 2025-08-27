// src/hooks/usePerImageTimeline.js
import { useRef, useState, useLayoutEffect, useCallback } from "react";
import axios from "axios";

export default function usePerImageTimeline(apiBase = "http://localhost:8000") {
  const [frames, setFrames] = useState([]);
  const [scrubT, setScrubT] = useState(null);

  const framesByImageRef = useRef(new Map());
  const tOffsetRef = useRef(0);
  const timelineRef = useRef(null);
  const timelineScrollRef = useRef(0);

  // --- API helpers ---
  const saveFramesForImage = useCallback(
    async (imageId, framesArr) => {
      if (!imageId) return;
      try {
        await axios.post(`${apiBase}/frames/${imageId}`, framesArr, {
          withCredentials: true, // keep cookies for auth
        });
        framesByImageRef.current.set(imageId, framesArr);
      } catch (err) {
        console.error("Failed to save frames to server:", err);
      }
    },
    [apiBase]
  );

  const loadFramesForImage = useCallback(
    async (imageId) => {
      if (!imageId) return [];
      try {
        const { data } = await axios.get(`${apiBase}/frames/${imageId}`, {
          withCredentials: true,
        });
        framesByImageRef.current.set(imageId, data);
        return data;
      } catch (err) {
        console.error("Failed to load frames from server:", err);
        return [];
      }
    },
    [apiBase]
  );


  // --- Scroll state (same as before) ---
  useLayoutEffect(() => {
    const el = timelineRef.current;
    if (el) el.scrollLeft = timelineScrollRef.current;
  }, [frames.length, scrubT]);

  const rememberScroll = useCallback(() => {
    const el = timelineRef.current;
    if (el) timelineScrollRef.current = el.scrollLeft;
  }, []);

  const restoreScroll = useCallback(() => {
    const el = timelineRef.current;
    if (el) el.scrollLeft = timelineScrollRef.current;
  }, []);

  const computeNextOffsetFrom = useCallback(
    (arr) => (arr.length ? arr[arr.length - 1].globalT + 1 : 0),
    []
  );

  return {
    frames,
    setFrames,
    scrubT,
    setScrubT,
    tOffsetRef,
    timelineRef,
    timelineScrollRef,
    saveFramesForImage,
    loadFramesForImage,
    rememberScroll,
    restoreScroll,
    computeNextOffsetFrom,
  };
}
