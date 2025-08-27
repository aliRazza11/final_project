export default function ImageCard({ title, src, placeholder = "No image" }) {
  return (
    <div className="bg-white rounded-2xl shadow-md border border-gray-200 flex flex-col overflow-hidden">
      <h2 className="text-xl md:text-2xl font-bold text-center text-gray-900 py-3 border-b border-gray-200">
        {title}
      </h2>
      <div className="flex-1 flex items-center justify-center p-2 overflow-hidden">
        {src ? (
          <img
          src={src}
          alt={title}
          className="max-h-full max-w-full object-contain"
          style={{ width: "800px", height: "600px", imageRendering: "pixelated"}}
          />
        ) : (
          <div
            className="text-gray-400 flex items-center justify-center text-xl"
            style={{ width: "800px", height: "600px" }}
          >
            {placeholder}
          </div>
        )}
      </div>
    </div>
  );
}
