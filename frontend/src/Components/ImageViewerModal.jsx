export default function ImageViewerModal({ image, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
      <div className="relative max-w-5xl max-h-[90vh] w-full flex flex-col items-center">
        <button
          onClick={onClose}
          className="absolute -top-10 right-0 text-white bg-black/60 rounded-full p-2 hover:bg-black/80 transition"
        >
          ✕
        </button>
        <img
          src={image.url}
          alt={image.name}
          className="max-h-[80vh] mx-auto rounded-lg object-contain shadow-lg"
        />
        <p className="text-center text-white mt-3 text-sm opacity-80">
          {image.name}
        </p>
      </div>
    </div>
  );
}
