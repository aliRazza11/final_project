import { useCallback } from "react";
import { toUiImage, fileToDataURL } from "../utils/image";

export default function useUploadImage({
  api,
  currentImageKey,
  frames,
  saveFramesForImage,
  switchToImage,
  addOrUpdate,
  refreshHistory,
}) {
  const handleUpload = useCallback(
    async (file) => {
      if (!file) return;
      if (!file.type?.startsWith?.("image/")) {
        alert("Please upload a valid image file (JPG, PNG, WEBP, etc.).");
        return;
      }

      if (currentImageKey) saveFramesForImage(currentImageKey, frames);


      const objectUrl = URL.createObjectURL(file);
      const dataUrl = await fileToDataURL(file);
      await switchToImage(null, objectUrl, dataUrl);

      try {
        const item = await api.images.upload(file);
        const uiItem = toUiImage(item);
        addOrUpdate(uiItem);
        await switchToImage(uiItem.id, uiItem.url, uiItem.url);
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

  return { handleUpload };
}
