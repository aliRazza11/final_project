import { useCallback } from "react";

export default function TimelineStrip({
  frames, scrubT, setScrubT,
  timelineRef, rememberScroll, restoreScroll,
  onCenterClick, onAfterSelect
}) {
  const handleWheel = useCallback((e) => {
    const el = timelineRef.current;
    if (!el) return;
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
      el.scrollLeft += e.deltaY;
      e.preventDefault();
    }
  }, [timelineRef]);

  return (
    <div ref={timelineRef} className="w-full overflow-x-auto" onWheel={handleWheel}>
      <div className="flex gap-2">
        {frames.map((f) => (
          <button
            key={f.globalT}
            onMouseDown={(e) => e.preventDefault()}
            tabIndex={-1}
            onClick={(e) => {
              rememberScroll();
              setScrubT(f.globalT);
              requestAnimationFrame(restoreScroll);
              onCenterClick?.(e);
              onAfterSelect?.();
            }}
            className={`relative flex-shrink-0 border rounded-md overflow-hidden ${
              scrubT === f.globalT ? "ring-2 ring-blue-500" : "hover:opacity-90"
            }`}
          >
            <img src={f.image} alt={`t=${f.localT}`} className="h-20 w-20 object-cover" style={{ imageRendering: "pixelated"}}/>
            <span className="absolute bottom-0 right-0 m-1 text-[10px] px-1.5 rounded bg-black/70 text-white">
              t{f.localT}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
