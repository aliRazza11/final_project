import struct
import numpy as np
import mysql.connector
from io import BytesIO
from PIL import Image
import random

# Paths to your downloaded MNIST ubyte files
TRAIN_IMAGES = r"mnist\train-images-idx3-ubyte"
TRAIN_LABELS = r"mnist\train-labels-idx1-ubyte"

# MySQL connection config
DB_CONFIG = {
    "user": "root",
    "password": "1234",
    "host": "127.0.0.1",
    "database": "diffusiondb",
}


def load_images(filename):
    with open(filename, "rb") as f:  # <-- fixed (no gzip)
        magic, num, rows, cols = struct.unpack(">IIII", f.read(16))
        buf = f.read(rows * cols * num)
        data = np.frombuffer(buf, dtype=np.uint8).reshape(num, rows, cols)
    return data


def load_labels(filename):
    with open(filename, "rb") as f:  # <-- fixed (no gzip)
        magic, num = struct.unpack(">II", f.read(8))
        buf = f.read(num)
        labels = np.frombuffer(buf, dtype=np.uint8)
    return labels


def image_to_png_bytes(image_array):
    """Convert a (28x28) numpy array into PNG bytes."""
    img = Image.fromarray(image_array, mode="L")  # grayscale
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def main():
    images = load_images(TRAIN_IMAGES)
    labels = load_labels(TRAIN_LABELS)

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    for digit in range(10):
        # Find indices of all samples for this digit
        indices = np.where(labels == digit)[0]
        # Pick 20 random indices
        chosen = random.sample(list(indices), 20)

        for sample_idx, img_idx in enumerate(chosen, start=1):
            img_bytes = image_to_png_bytes(images[img_idx])

            cursor.execute(
                """
                INSERT INTO mnist (digit, sample_index, image_data)
                VALUES (%s, %s, %s)
                """,
                (digit, sample_idx, img_bytes),
            )

        print(f"Inserted 20 samples for digit {digit}")

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
