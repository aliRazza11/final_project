// src/Pages/Dashboard/dashboard.jsx
import React, { useState, useEffect, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";

import Sidebar from "../../Components/Sidebar";
import NoticeModal from "../../Components/NoticeModal";
import UploadButton from "../../Components/UploadButton";
import ImageCard from "../../Components/ImageCard";
import Controls from "../../Components/Controls";
import DeleteModal from "../../Components/DeleteModal";
import ImageViewerModal from "../../Components/ImageViewerModal";
import TimelineStrip from "../../Components/TimelineStrip";
import NoiseChart from "../../Components/NoiseChart";
import BetaChart from "../../Components/BetaChart";

import useImageHistory from "../../hooks/useImageHistory";
import usePerImageTimeline from "../../hooks/usePerImageTimeline";
import useDiffusionOrchestrator from "../../hooks/useDiffusionOrchestrator";
import useMnistPicker from "../../hooks/useMnistPicker";

import { api } from "../../services/api";
import { toUiImage } from "../../utils/image";
import { centerThumb } from "../../utils/timeline";

// NEW slim helpers
import useImageSwitch from "../../hooks/useImageSwitch";
import useUploadImage from "../../hooks/useUploadImage";
import useDeleteImage from "../../hooks/useDeleteImage";
import useChartPoints from "../../hooks/useChartPoints";

export default function Dashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const preloaded = location.state?.image;

  // Sidebar/UI state
  const [collapsed, setCollapsed] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedForDelete, setSelectedForDelete] = useState(null);
  const [viewerImage, setViewerImage] = useState(null);

  const [analysisAvailable, setAnalysisAvailable] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);

  // Active image session
  const [uploadedImage, setUploadedImage] = useState(null);
  const [uploadedImageDataUrl, setUploadedImageDataUrl] = useState(null);
  const [currentImageKey, setCurrentImageKey] = useState(null);

  // Timeline storage
  const {
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
  } = usePerImageTimeline();

  const chartPoints = useChartPoints(frames);

  // Diffusion orchestration
  const {
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
  } = useDiffusionOrchestrator({
    api,
    uploadedImageDataUrl,
    currentImageKey,
    frames,
    setFrames,
    saveFramesForImage,
    deleteFramesForImage,
    tOffsetRef,
  });

  // History
  const { history, refreshHistory, removeById, addOrUpdate } = useImageHistory();

  // MNIST
  const {
    showMnistSelector,
    mnistDigit,
    mnistImages,
    mnistLoading,
    mnistError,
    openMnistSelector,
    closeMnistSelector,
    handleChooseMnistDigit,
    handlePickMnistImage,
    setMnistImages,
    setMnistDigit,
    setMnistError,
  } = useMnistPicker({
    api,
    onAfterUpload: async (uiItem) => {
      addOrUpdate(uiItem);
      await switchToImage(uiItem.id, uiItem.url, uiItem.url);
      refreshHistory();
    },
  });

  // Image switching / upload / delete moved out
  const { switchToImage } = useImageSwitch({
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
  });

  const { handleUpload } = useUploadImage({
    api,
    currentImageKey,
    frames,
    saveFramesForImage,
    switchToImage,
    addOrUpdate,
    refreshHistory,
  });

  const { confirmDelete } = useDeleteImage({
    api,
    currentImageKey,
    deleteFramesForImage,
    switchToImage,
    removeById,
    refreshHistory,
    setUploadedImage,
    setSelectedForDelete,
    setShowDeleteModal,
  });

  const canDiffuse = Boolean(uploadedImageDataUrl);

  // Preload from router state
  useEffect(() => {
    if (!preloaded) return;
    (async () => {
      const key = preloaded.id || `preloaded:${preloaded.url?.slice(0, 64)}`;
      await switchToImage(key, preloaded.url, preloaded.url);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preloaded]);

  // Cleanup WS on unmount
  useEffect(
    () => () => {
      try {
        wsRef.current?.close();
      } catch {}
    },
    [wsRef]
  );

  // Update preview when scrubbing
  useEffect(() => {
    if (scrubT == null) return;
    const f = frames.find((x) => x.globalT === scrubT);
    if (f?.image) setDiffusedImage(f.image);
  }, [scrubT, frames, setDiffusedImage]);

  // small local handlers that are still readable
  const handleSelectFromSidebar = useCallback(
    (item) => {
      const ui = toUiImage(item);
      switchToImage(ui.id, ui.url, ui.url);
    },
    [switchToImage]
  );

  const onCenterThumb = useCallback(
    (e) => centerThumb(e, timelineRef, timelineScrollRef),
    [timelineRef, timelineScrollRef]
  );

  const handleSetScrubT = useCallback(
    (t) => {
      setScrubT(t);
      if (t != null) setFollowStream(false);
    },
    [setScrubT, setFollowStream]
  );

  const handleCloseAnalysis = useCallback(() => {
    setShowAnalysis(false);
    setFollowStream(true);
    setScrubT(null);
  }, [setScrubT, setFollowStream]);

  const handleLogout = useCallback(async () => {
    try {
      await api.auth.logout();
      navigate("/login", { replace: true });
      window.location.reload();
    } catch (e) {
      console.error("Error logging out:", e);
    }
  }, [navigate]);

  return (
    // 🔽 your full existing JSX return stays here unchanged 🔽
    <div className="h-screen w-screen overflow-hidden bg-gray-100 text-gray-900">
      {/* Sidebar */}
      <Sidebar
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        history={history}
        onSelectItem={handleSelectFromSidebar}
        onDeleteItem={(item) => {
          setSelectedForDelete(item);
          setShowDeleteModal(true);
        }}
        onSettings={() => navigate("/settings")}
        onLogout={handleLogout}
      />

      {/* Main content */}
      <div
        className="flex flex-col overflow-y-auto h-screen"
        style={{ marginLeft: collapsed ? "4rem" : "16rem" }}
      >
        <main className="flex flex-col">
          {!uploadedImage ? (
            <div className="flex-1 flex flex-col items-center justify-center p-6">
              <label className="flex flex-col items-center justify-center w-full max-w-lg h-64 border-2 border-dashed border-gray-400 rounded-2xl cursor-pointer bg-gray-50 hover:bg-gray-100">
                <UploadButton onSelect={handleUpload} label="Choose File" />
                <p className="mt-3 text-sm text-gray-500">
                  Drag & drop an image here, or click to select
                </p>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleUpload(e.target.files[0])}
                  className="hidden"
                />
              </label>

              <div className="mt-4 flex items-center gap-3">
                <button
                  onClick={openMnistSelector}
                  className="px-4 py-2 rounded-lg bg-gray-900 text-white text-sm font-bold hover:bg-gray-800"
                >
                  Choose MNIST Digit
                </button>
                <button
                  onClick={refreshHistory}
                  className="text-sm text-gray-600 underline hover:no-underline"
                >
                  Refresh history
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Primary image view */}
              <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6 p-6">
                {/* Original */}
                <div className="flex flex-col gap-3">
                  <ImageCard title="Original Image" src={uploadedImage} />
                  <div className="flex justify-center mt-2 gap-3">
                    <UploadButton onSelect={handleUpload} label="Upload Image" compact />
                    <button
                      onClick={openMnistSelector}
                      className="px-3 py-2 rounded-lg bg-gray-800 text-white text-sm font-bold hover:bg-gray-700"
                    >
                      Pick MNIST
                    </button>
                  </div>
                </div>

                {/* Diffused */}
                <div className="flex flex-col gap-3">
                  <ImageCard
                    title={
                      mode === "slow"
                        ? `Diffused Image ${isStreaming ? `(step ${currentStep} / ${totalSteps})` : ""}`
                        : "Diffused Image"
                    }
                    src={diffusedImage}
                    placeholder="Click Diffuse to generate image"
                  />

                  <div className="flex justify-center gap-3 mt-2">
                    <button
                      onClick={() => {
                        setAnalysisAvailable(true);
                        diffuse();
                      }}
                      disabled={!canDiffuse}
                      className={`px-4 py-2 rounded-lg text-sm font-bold ${
                        canDiffuse
                          ? "bg-gray-900 text-white hover:bg-gray-800"
                          : "bg-gray-400 text-gray-200 cursor-not-allowed"
                      }`}
                    >
                      Diffuse
                    </button>

                    {mode === "slow" && isStreaming && (
                      <button
                        onClick={cancelStream}
                        className="px-4 py-2 rounded-lg font-bold bg-red-600 text-white text-sm hover:bg-red-700"
                      >
                        Cancel
                      </button>
                    )}

                    {analysisAvailable && (
                      <button
                        onClick={() => setShowAnalysis(true)}
                        className="px-4 py-2 rounded-lg bg-gray-900 text-white text-sm font-bold hover:bg-gray-800"
                      >
                        View Timeline & Graphs
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Controls */}
              <div className="bottom-0 bg-white border-t p-6">
                <Controls
                  diffusion={diffusion}
                  setDiffusion={setDiffusion}
                  mode={mode}
                  setMode={setMode}
                />
              </div>
            </>
          )}
        </main>
      </div>

      {/* Delete confirmation */}
      {showDeleteModal && (
        <DeleteModal
          file={selectedForDelete}
          onCancel={() => {
            setSelectedForDelete(null);
            setShowDeleteModal(false);
          }}
          onConfirm={() => confirmDelete(selectedForDelete)}
        />
      )}

      {/* Image Viewer */}
      {viewerImage && (
        <ImageViewerModal image={viewerImage} onClose={() => setViewerImage(null)} />
      )}

      {/* 🔥 Analysis Modal */}
      {showAnalysis && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-5xl max-h-[90vh] overflow-y-auto p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Timeline & Analysis</h2>
              <button
                onClick={() => {
                  setShowAnalysis(false);
                  setFollowStream(true);
                  setScrubT(null);
                }}
                className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 text-sm"
              >
                Close
              </button>
            </div>

            {/* Compact thumbnails */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="border rounded-lg bg-white p-2">
                <img src={uploadedImage} alt="Original" className="w-full h-40 object-contain" />
                <p className="text-center text-sm mt-1">Original</p>
              </div>
              <div className="border rounded-lg bg-white p-2">
                <img
                  src={diffusedImage}
                  alt="Diffused"
                  style={{ imageRendering: "pixelated" }}
                  className="w-full h-40 object-contain"
                />
                <p className="text-center text-sm mt-1">Diffused</p>
              </div>
            </div>

            {/* Timeline */}
            <TimelineStrip
              frames={frames}
              scrubT={scrubT}
              setScrubT={(t) => {
                setScrubT(t);
                if (t != null) setFollowStream(false);
              }}
              timelineRef={timelineRef}
              rememberScroll={rememberScroll}
              restoreScroll={restoreScroll}
              onCenterClick={(e) => centerThumb(e, timelineRef, timelineScrollRef)}
            />

            {/* Charts */}
            <div className="mt-6">
              <NoiseChart chartPoints={chartPoints} scrubT={scrubT} setScrubT={setScrubT} />
              <BetaChart chartPoints={chartPoints} scrubT={scrubT} setScrubT={setScrubT} />
            </div>
          </div>
        </div>
      )}

      {/* 🧠 MNIST Selector Modal */}
      {showMnistSelector && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-5xl max-h-[90vh] overflow-y-auto p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">
                {mnistImages.length
                  ? `Select an MNIST image for digit ${mnistDigit}`
                  : "Select an MNIST Digit"}
              </h2>
              <button
                onClick={closeMnistSelector}
                className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 text-sm"
              >
                Close
              </button>
            </div>

            {!mnistImages.length ? (
              <>
                {mnistError && <p className="text-sm text-red-600 mb-3">{mnistError}</p>}
                <div className="grid grid-cols-5 gap-2">
                  {Array.from({ length: 10 }).map((_, d) => (
                    <button
                      key={d}
                      onClick={() => handleChooseMnistDigit(d)}
                      className={`px-3 py-2 border rounded-lg text-sm font-bold ${
                        mnistDigit === d ? "bg-gray-900 text-white" : "bg-gray-100 hover:bg-gray-200"
                      }`}
                      disabled={mnistLoading}
                    >
                      {mnistLoading && mnistDigit === d ? "Loading…" : d}
                    </button>
                  ))}
                </div>
                <p className="mt-4 text-xs text-gray-500">
                  Pick a digit to load 20 sample images from your `/images/digit` endpoint.
                </p>
              </>
            ) : (
              <>
                {mnistError && <p className="text-sm text-red-600 mb-3">{mnistError}</p>}
                <div className="grid grid-cols-5 gap-4">
                  {mnistImages.map((img) => (
                    <button
                      key={img.id}
                      onClick={() => handlePickMnistImage(img)}
                      className="border rounded-lg overflow-hidden hover:ring-2 hover:ring-gray-600 bg-white"
                      title={`Digit ${img.digit} • Sample ${img.sample_index}`}
                    >
                      <img
                        src={`data:image/png;base64,${img.image_data}`}
                        alt={`MNIST ${img.digit}`}
                        className="w-24 h-24 object-contain mx-auto my-2"
                      />
                      <div className="text-center text-xs text-gray-600 mb-2">
                        #{img.sample_index}
                      </div>
                    </button>
                  ))}
                </div>

                <div className="flex justify-between items-center mt-6">
                  <button
                    onClick={() => {
                      setMnistImages([]);
                      setMnistError("");
                    }}
                    className="px-4 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 text-sm"
                  >
                    Back
                  </button>
                  <button
                    onClick={closeMnistSelector}
                    className="px-4 py-2 rounded-lg bg-gray-900 text-white text-sm font-bold hover:bg-gray-800"
                  >
                    Done
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
