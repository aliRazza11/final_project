// src/utils/timeline.js

/**
 * Centers the clicked thumbnail within the timeline container.
 */
export function centerThumb(event, timelineRef, timelineScrollRef) {
  const el = timelineRef.current;
  if (!el) return;
  const crect = el.getBoundingClientRect();
  const brect = event.currentTarget.getBoundingClientRect();
  const delta = brect.left - (crect.left + crect.width / 2 - brect.width / 2);
  el.scrollLeft += delta;
  timelineScrollRef.current = el.scrollLeft;
}
