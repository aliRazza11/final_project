// src/Pages/Dashboard/dashboard.jsx
import React, { useMemo, useState, useEffect, useCallback } from "react";
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
import useDiffusionStream from "../../hooks/useDiffusionStream";

import { api } from "../../services/api";
import { toUiImage, fileToDataURL, clamp } from "../../utils/image";

export default function Dashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const preloaded = location.state?.image;

  // UI state
  const [collapsed, setCollapsed] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedForDelete, setSelectedForDelete] = useState(null);
  const [viewerImage, setViewerImage] = useState(null);

  const [analysisAvailable, setAnalysisAvailable] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);

  const [uploadedImage, setUploadedImage] = useState(null);
  const [uploadedImageDataUrl, setUploadedImageDataUrl] = useState(null);
  const [currentImageKey, setCurrentImageKey] = useState(null);

  // Diffusion config + view
  const [diffusedImage, setDiffusedImage] = useState(null);
  const [diffusion, setDiffusion] = useState({
    steps: 500,
    betaMin: "",
    betaMax: "",
    schedule: "linear",
  });
  const [mode, setMode] = useState("slow");

  // Streaming state
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [streamError, setStreamError] = useState("");

  // Invalid file modal
  const [invalidFileOpen, setInvalidFileOpen] = useState(false);
  const [invalidFileMsg, setInvalidFileMsg] = useState("");

  // --- MNIST picker state ---
  const [showMnistSelector, setShowMnistSelector] = useState(false);
  const [mnistDigit, setMnistDigit] = useState(null);
  const [mnistImages, setMnistImages] = useState([]);
  const [mnistLoading, setMnistLoading] = useState(false);
  const [mnistError, setMnistError] = useState("");

  // Per-image timeline (IndexedDB-backed)
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

  // Diffusion streaming (REST + WS)
  const { fastDiffuse, slowDiffuse, cancel: cancelStream, wsRef } = useDiffusionStream({ api });

  // History store (list on sidebar)
  const { history, refreshHistory, removeById, addOrUpdate } = useImageHistory();

  const canDiffuse = Boolean(uploadedImageDataUrl);

  // --- Live follow flag ---
  const [followStream, setFollowStream] = useState(true);

  // Derived chart data
  const chartPoints = useMemo(
    () =>
      frames
        .map((f) => {
          const c = f?.metrics?.Cosine;
          const b = f?.betas;
          return {
            x: f.globalT,
            residual: typeof c === "number" && isFinite(c) ? 1 - c : null,
            beta: typeof b === "number" && isFinite(b) ? b : null,
          };
        })
        .filter((p) => p.residual !== null || p.beta !== null),
    [frames]
  );

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

  // Update preview when scrubbing (explicit user control)
  useEffect(() => {
    if (scrubT == null) return;
    const f = frames.find((x) => x.globalT === scrubT);
    if (f?.image) setDiffusedImage(f.image);
    if (typeof f?.localT === "number") setCurrentStep(f.localT);
  }, [scrubT, frames]);

  const switchToImage = useCallback(
    async (key, imageUrl, dataUrl) => {
      // stop any running stream
      try {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ action: "cancel" }));
          wsRef.current.close();
        }
      } catch {}

      setIsStreaming(false);
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
      setCurrentStep(0);
      tOffsetRef.current = computeNextOffsetFrom(restored);

      // restore preview from last frame
      if (restored.length) {
        const last = restored[restored.length - 1];
        if (last?.image) setDiffusedImage(last.image);
      } else {
        setDiffusedImage(null);
      }

      // switching images resets analysis availability until you run again
      setAnalysisAvailable(restored.length > 0);
      setFollowStream(true);
    },
    [
      wsRef,
      currentImageKey,
      frames,
      saveFramesForImage,
      loadFramesForImage,
      setFrames,
      setScrubT,
      computeNextOffsetFrom,
      tOffsetRef,
    ]
  );

  const handleUpload = useCallback(
    async (file) => {
      if (!file) return;
      if (!file.type.startsWith("image/")) {
        setInvalidFileMsg("Please upload a valid image file (JPG, PNG, WEBP, etc.).");
        setInvalidFileOpen(true);
        return;
      }

      // persist current image’s frames
      if (currentImageKey) saveFramesForImage(currentImageKey, frames);

      // temp preview
      const objectUrl = URL.createObjectURL(file);
      const dataUrl = await fileToDataURL(file);

      // switch immediately (no key yet)
      await switchToImage(null, objectUrl, dataUrl);

      try {
        const item = await api.uploadImage(file);
        const uiItem = toUiImage(item);

        // Add to sidebar immediately
        addOrUpdate(uiItem);

        // switch with stable id
        await switchToImage(uiItem.id, uiItem.url, uiItem.url);

        // optional sync
        refreshHistory();
      } catch (err) {
        console.error(err);
      } finally {
        URL.revokeObjectURL(objectUrl);
      }
    },
    [
      api,
      currentImageKey,
      frames,
      saveFramesForImage,
      switchToImage,
      addOrUpdate,
      refreshHistory,
    ]
  );

  const handleSelectFromSidebar = useCallback(
    (item) => {
      const ui = toUiImage(item);
      switchToImage(ui.id, ui.url, ui.url);
    },
    [switchToImage]
  );

  const confirmDelete = useCallback(async () => {
    if (!selectedForDelete) return;
    const id = selectedForDelete.id;

    // If deleting active image, clear its timeline
    if (currentImageKey === id) {
      await deleteFramesForImage(id);
      await switchToImage(null, null, null);
    }

    // optimistic removal from sidebar
    removeById(id);

    try {
      await api.deleteImage(id);
      refreshHistory();
      setUploadedImage(null);
    } catch (e) {
      console.error("Delete failed:", e);
    } finally {
      setSelectedForDelete(null);
      setShowDeleteModal(false);
    }
  }, [
    selectedForDelete,
    currentImageKey,
    deleteFramesForImage,
    removeById,
    refreshHistory,
    switchToImage,
  ]);

  // Reset timeline completely before starting a new slow run
  const resetTimelineForActiveImage = useCallback(async () => {
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: "cancel" }));
        wsRef.current.close();
      }
    } catch {}

    if (currentImageKey) {
      await deleteFramesForImage(currentImageKey);
    }

    setFrames([]);
    setScrubT(null);
    setCurrentStep(0);
    setDiffusedImage(null);
    tOffsetRef.current = 0;
    setFollowStream(true); // new run -> follow live by default
  }, [
    currentImageKey,
    deleteFramesForImage,
    setFrames,
    setScrubT,
    setCurrentStep,
    setDiffusedImage,
    tOffsetRef,
    wsRef,
  ]);

  const diffuse = useCallback(async () => {
    if (!canDiffuse) {
      setInvalidFileMsg("Please upload an image first.");
      setInvalidFileOpen(true);
      return;
    }

    // Clicking Diffuse enables the analysis button immediately
    setAnalysisAvailable(true);

    if (mode === "fast") {
      setStreamError("");
      setIsStreaming(false);
      setFollowStream(true);
      await fastDiffuse({
        uploadedImageDataUrl,
        diffusion,
        setDiffusedImage, // fast returns a single image
        setCurrentStep,
      });
      return;
    }

    // SLOW (WebSocket) — clear old timeline, then stream fresh
    await resetTimelineForActiveImage();

    setStreamError("");
    setIsStreaming(true);
    setFollowStream(true);

    const nextOffset = 0;
    tOffsetRef.current = nextOffset;

    slowDiffuse({
      uploadedImageDataUrl,
      diffusion,
      tOffset: nextOffset,
      onStart: () => {},
      onFrame: async (frame) => {
        if (!frame.image) return;

        // Keep a complete timeline
        setFrames((prev) => {
          const idx = prev.findIndex((f) => f.globalT === frame.globalT);
          const next =
            idx >= 0
              ? prev.map((p, i) => (i === idx ? frame : p))
              : [...prev, frame].sort((a, b) => a.globalT - b.globalT);

          if (currentImageKey) {
            saveFramesForImage(currentImageKey, next);
          }
          return next;
        });

        // Live streaming into the Diffused Image card
        if (followStream && frame.image) {
          setDiffusedImage(frame.image);
        }
      },
      onProgress: (p, t) => {
        setCurrentStep(t);
      },
      onDone: () => {
        setIsStreaming(false);
      },
      onError: (err) => {
        setIsStreaming(false);
        setStreamError(err?.message || "WebSocket error");
      },
    });
  }, [
    mode,
    canDiffuse,
    fastDiffuse,
    slowDiffuse,
    uploadedImageDataUrl,
    diffusion,
    resetTimelineForActiveImage,
    setDiffusedImage,
    setCurrentStep,
    tOffsetRef,
    currentImageKey,
    saveFramesForImage,
    setFrames,
    setStreamError,
    setIsStreaming,
    followStream,
  ]);

  const onCenterThumb = useCallback(
    (e) => {
      const el = timelineRef.current;
      if (!el) return;
      const crect = el.getBoundingClientRect();
      const brect = e.currentTarget.getBoundingClientRect();
      const delta = brect.left - (crect.left + crect.width / 2 - brect.width / 2);
      el.scrollLeft += delta;
      timelineScrollRef.current = el.scrollLeft;
    },
    [timelineRef, timelineScrollRef]
  );

  // Wrap setScrubT so we can pause live following while the user scrubs
  const handleSetScrubT = useCallback(
    (t) => {
      setScrubT(t);
      if (t != null) setFollowStream(false);
    },
    [setScrubT]
  );

  const handleCloseAnalysis = useCallback(() => {
    setShowAnalysis(false);
    setFollowStream(true);
    setScrubT(null);
  }, [setScrubT]);

  const handleLogout = useCallback(async () => {
    try {
      await api.logout();
      navigate("/login", { replace: true });
      window.location.reload();
    } catch (e) {
      console.error("Error logging out:", e);
    }
  }, [navigate]);

  // --- MNIST handlers ---
  const openMnistSelector = useCallback(() => {
    setShowMnistSelector(true);
    setMnistDigit(null);
    setMnistImages([]);
    setMnistLoading(false);
    setMnistError("");
  }, []);

  const fetchMnistForDigit = useCallback(
    async (d) => {
      setMnistLoading(true);
      setMnistError("");
      try {
        // Expecting: [{ id, digit, sample_index, image_data }, ...] (20 items)
        const res = await api.get(`/images/digit/${d}`);
        // if your api wrapper returns {data}, use res.data
        const list = Array.isArray(res?.data) ? res.data : Array.isArray(res) ? res : [];
        setMnistImages(list);
      } catch (e) {
        console.error(e);
        setMnistError("Failed to load MNIST samples. Please try again.");
      } finally {
        setMnistLoading(false);
      }
    },
    [setMnistImages]
  );

  const handleChooseMnistDigit = useCallback(
    async (d) => {
      setMnistDigit(d);
      await fetchMnistForDigit(d);
    },
    [fetchMnistForDigit]
  );

const handlePickMnistImage = useCallback(
  async (img) => {
    try {
      // Convert base64 → Blob
      const byteCharacters = atob(img.image_data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: "image/png" });

      // Wrap in a File (so api.uploadImage works)
      const file = new File([blob], `mnist-${img.digit}-${img.sample_index}.png`, {
        type: "image/png",
      });

      // Upload to backend (will persist in DB)
      const item = await api.uploadImage(file);
      const uiItem = toUiImage(item);

      // Add to sidebar immediately
      addOrUpdate(uiItem);

      // Switch to the uploaded image (stable id from DB)
      await switchToImage(uiItem.id, uiItem.url, uiItem.url);

      // Refresh history from server (optional sync)
      refreshHistory();

      // Close modal
      setShowMnistSelector(false);
      setMnistImages([]);
      setMnistDigit(null);
    } catch (err) {
      console.error("Failed to pick MNIST image:", err);
    }
  },
  [switchToImage, addOrUpdate, refreshHistory]
);


  const totalSteps = clamp(Number(diffusion.steps) || 1, 1, 1000);

  // --- RENDER ---
  return (
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
                      onClick={diffuse}
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
          onConfirm={confirmDelete}
        />
      )}

      {/* Image Viewer */}
      {viewerImage && <ImageViewerModal image={viewerImage} onClose={() => setViewerImage(null)} />}

      {/* Invalid file modal */}
      <NoticeModal
        open={invalidFileOpen}
        title="Invalid file type"
        message={invalidFileMsg}
        onClose={() => setInvalidFileOpen(false)}
      />

      {/* 🔥 Analysis Modal */}
      {showAnalysis && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-5xl max-h-[90vh] overflow-y-auto p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Timeline & Analysis</h2>
              <button
                onClick={handleCloseAnalysis}
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
                <img src={diffusedImage} alt="Diffused" style={{imageRendering:"pixelated"}}className="w-full h-40 object-contain" />
                <p className="text-center text-sm mt-1">Diffused</p>
              </div>
            </div>

            {/* Timeline */}
            <TimelineStrip
              frames={frames}
              scrubT={scrubT}
              setScrubT={handleSetScrubT}
              timelineRef={timelineRef}
              rememberScroll={rememberScroll}
              restoreScroll={restoreScroll}
              onCenterClick={onCenterThumb}
            />

            {/* Charts */}
            <div className="mt-6">
              <NoiseChart chartPoints={chartPoints} scrubT={scrubT} setScrubT={handleSetScrubT} />
              <BetaChart chartPoints={chartPoints} scrubT={scrubT} setScrubT={handleSetScrubT} />
            </div>
          </div>
        </div>
      )}

      {/* 🧠 MNIST Selector Modal (two-step: choose digit → choose one of 20 samples) */}
      {showMnistSelector && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-5xl max-h-[90vh] overflow-y-auto p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">
                {mnistImages.length ? `Select an MNIST image for digit ${mnistDigit}` : "Select an MNIST Digit"}
              </h2>
              <button
                onClick={() => {
                  setShowMnistSelector(false);
                  setMnistImages([]);
                  setMnistDigit(null);
                  setMnistError("");
                }}
                className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 text-sm"
              >
                Close
              </button>
            </div>

            {!mnistImages.length ? (
              <>
                {mnistError && (
                  <p className="text-sm text-red-600 mb-3">{mnistError}</p>
                )}
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
                {mnistError && (
                  <p className="text-sm text-red-600 mb-3">{mnistError}</p>
                )}
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
                    onClick={() => {
                      setShowMnistSelector(false);
                      setMnistImages([]);
                      setMnistDigit(null);
                      setMnistError("");
                    }}
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
