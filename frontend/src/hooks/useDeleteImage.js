// src/hooks/useDeleteImage.js
import { useCallback } from "react";

/**
 * Delete handler with optimistic sidebar removal and timeline cleanup.
 */
export default function useDeleteImage({
  api,
  currentImageKey,
  switchToImage,
  removeById,
  refreshHistory,
  setUploadedImage,
  setSelectedForDelete,
  setShowDeleteModal,
}) {
  const confirmDelete = useCallback(
    async (selectedForDelete) => {
      if (!selectedForDelete) return;
      const id = selectedForDelete.id;


      // optimistic removal
      removeById(id);

      try {
        await api.images.remove(id);
        refreshHistory();
        setUploadedImage(null);
      } catch (e) {
        console.error("Delete failed:", e);
      } finally {
        setSelectedForDelete?.(null);
        setShowDeleteModal?.(false);
      }
    },
    [
      api,
      currentImageKey,
      switchToImage,
      removeById,
      refreshHistory,
      setUploadedImage,
      setSelectedForDelete,
      setShowDeleteModal,
    ]
  );

  return { confirmDelete };
}
