import mysql.connector
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt

# MySQL connection config
DB_CONFIG = {
    "user": "root",              # or mnistuser if you created one
    "password": "1234",
    "host": "127.0.0.1",
    "database": "diffusiondb",
}


def fetch_image(digit: int, sample_index: int):
    """Fetch image bytes for a given digit + sample index."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT image_data FROM mnist
        WHERE digit = %s AND sample_index = %s
        """,
        (digit, sample_index),
    )

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        return row[0]  # image_data
    return None


def display_image(img_bytes: bytes):
    """Display PNG bytes as an image."""
    img = Image.open(BytesIO(img_bytes))
    plt.imshow(img, cmap="gray")
    plt.axis("off")
    plt.show()


if __name__ == "__main__":
    # Example: show digit=3, sample_index=5
    digit = 1
    sample_index = 1

    img_bytes = fetch_image(digit, sample_index)
    if img_bytes:
        display_image(img_bytes)
    else:
        print(f"No image found for digit={digit}, sample_index={sample_index}")
