import requests
from PIL import Image
import base64
import io
import matplotlib.pyplot as plt

session = requests.Session()
BASE_URL = "http://localhost:8000"

signup_cred = {
    "email": "apptester@test.com",
    "username": "tester",
    "password": "test1234"
}

login_cred = {
    "email": "apptester@test.com",
    "password": "test1234"
}

with Image.open("backend\_tests\images\img97.jpg") as img:
    img.thumbnail((256, 256))
    
    # Save to bytes buffer (compressed JPEG)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=70)
    image_bytes = buffer.getvalue()

image_base64 = base64.b64encode(image_bytes).decode("utf-8")
# print(image_base64[0:50])
payload = {
    "image_data": image_base64
}

# r = requests.post(f"{BASE_URL}/auth/signup",json=signup_cred)


r = session.post(f"{BASE_URL}/auth/login",json=login_cred)
print(r.status_code)

r = session.post(f"{BASE_URL}/auth/upload", json=payload)

res = session.get(f"{BASE_URL}/auth/upload")
# print(res.json())
response = res.json()
print(response)
back_img = base64.b64decode(response[0]["image_data"])
img = Image.open(io.BytesIO(back_img))
plt.imshow(img)
plt.show()