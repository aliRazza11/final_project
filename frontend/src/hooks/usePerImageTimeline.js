// src/hooks/usePerImageTimeline.js
import { useRef, useState, useLayoutEffect, useCallback } from "react";
import { set, get, del } from "idb-keyval";

export default function usePerImageTimeline() {
  const [frames, setFrames] = useState([]);
  const [scrubT, setScrubT] = useState(null);

  const framesByImageRef = useRef(new Map());
  const tOffsetRef = useRef(0);
  const timelineRef = useRef(null);
  const timelineScrollRef = useRef(0);

  // Use a cleaner naming scheme: "timeline:<imageId>"
  const dbKey = useCallback((imageId) => `timeline:${imageId}`, []);

  const saveFramesForImage = useCallback(
    async (imageId, framesArr) => {
      if (!imageId) return;
      framesByImageRef.current.set(imageId, framesArr);
      try {
        await set(dbKey(imageId), framesArr);
      } catch (err) {
        console.error("Failed to save frames in IndexedDB:", err);
      }
    },
    [dbKey]
  );

  const loadFramesForImage = useCallback(
    async (imageId) => {
      if (!imageId) return [];
      const mem = framesByImageRef.current.get(imageId);
      if (mem) return mem;
      try {
        const fromDb = await get(dbKey(imageId));
        return fromDb || [];
      } catch (err) {
        console.error("Failed to load frames from IndexedDB:", err);
        return [];
      }
    },
    [dbKey]
  );

  const deleteFramesForImage = useCallback(
    async (imageId) => {
      framesByImageRef.current.delete(imageId);
      try {
        await del(dbKey(imageId));
      } catch (err) {
        console.error("Failed to delete frames from IndexedDB:", err);
      }
    },
    [dbKey]
  );

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
    deleteFramesForImage,
    rememberScroll,
    restoreScroll,
    computeNextOffsetFrom,
  };
}
