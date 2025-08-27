export default function ProgressBar({ isStreaming, progress, currentStep, totalSteps, streamError }) {
  return (
    <div className="w-full max-w-xl mx-auto mt-4">
      <div className="h-2 rounded-full bg-gray-200 overflow-hidden">
        <div
          className="h-full bg-gray-900 transition-all"
          style={{ width: `${Math.round(progress * 100)}%` }}
        />
      </div>
      <div className="mt-1 text-xs text-gray-600 text-center">
        {isStreaming
          ? `Streaming… step ${currentStep} / ${totalSteps - 1}`
          : progress === 1
          ? "Done"
          : ""}
      </div>
      {streamError && (
        <div className="mt-2 text-xs text-red-600">{streamError}</div>
      )}
    </div>
  );
}
