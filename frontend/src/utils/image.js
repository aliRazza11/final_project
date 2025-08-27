export const toUiImage = (item) => ({
  id: item.id,
  name: item.filename,
  url: `data:${item.content_type};base64,${item.image_data}`,
  downloadHref: `http://localhost:8000/images/${item.id}`,
});

export const fileToDataURL = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

export const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
