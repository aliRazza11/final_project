import { useCallback, useState } from "react";
import { base64ToPngFile } from "../utils/file";
import { toUiImage } from "../utils/image";


export default function useMnistPicker({ api, onAfterUpload }) {
  const [showMnistSelector, setShowMnistSelector] = useState(false);
  const [mnistDigit, setMnistDigit] = useState(null);
  const [mnistImages, setMnistImages] = useState([]);
  const [mnistLoading, setMnistLoading] = useState(false);
  const [mnistError, setMnistError] = useState("");

  const openMnistSelector = useCallback(() => {
    setShowMnistSelector(true);
    setMnistDigit(null);
    setMnistImages([]);
    setMnistLoading(false);
    setMnistError("");
  }, []);

  const closeMnistSelector = useCallback(() => {
    setShowMnistSelector(false);
    setMnistDigit(null);
    setMnistImages([]);
    setMnistError("");
  }, []);

  const fetchMnistForDigit = useCallback(
    async (d) => {
      setMnistLoading(true);
      setMnistError("");
      try {
        // returns array [{ id, digit, sample_index, image_data }, ...]
        const list = await api.images.byDigit(d);
        const arr = Array.isArray(list?.data) ? list.data : Array.isArray(list) ? list : [];
        setMnistImages(arr);
      } catch (e) {
        console.error(e);
        setMnistError("Failed to load MNIST samples. Please try again.");
      } finally {
        setMnistLoading(false);
      }
    },
    [api]
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
        // Convert base64 (no header) -> File
        const file = base64ToPngFile(
          img.image_data,
          `mnist-${img.digit}-${img.sample_index}.png`
        );

        // Upload to backend (persist)
        const item = await api.images.upload(file);
        const uiItem = toUiImage(item);

        // Let the page switch image & refresh history
        await onAfterUpload(uiItem);

        // Reset UI
        closeMnistSelector();
      } catch (err) {
        console.error("Failed to pick MNIST image:", err);
        setMnistError("Upload failed. Try another sample.");
      }
    },
    [api, onAfterUpload, closeMnistSelector]
  );

  return {
    // state
    showMnistSelector,
    mnistDigit,
    mnistImages,
    mnistLoading,
    mnistError,

    // actions
    openMnistSelector,
    closeMnistSelector,
    handleChooseMnistDigit,
    handlePickMnistImage,

    // setters (if page needs them)
    setMnistImages,
    setMnistDigit,
    setMnistError,
  };
}
