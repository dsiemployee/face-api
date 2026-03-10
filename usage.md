# Face Verification API

This API verifies if two faces belong to the exact same person. It performs a **deep analysis** using `ArcFace` and `RetinaFace` via `deepface`. 

It includes privacy features like true in-memory processing (no images saved) and built-in mirror image handling.

## Deployment on Railway
1. Push this `backend` folder to a GitHub repository.
2. Go to [Railway.app](https://railway.app/).
3. Create a new project -> **Deploy from GitHub repo**.
4. Railway will automatically detect the `Dockerfile` and start building the Image.
5. In the Railway dashboard for the service, go to **Settings > Domains** and generate a custom domain (e.g., `face-api.up.railway.app`).

---

## Endpoint Usage

**Endpoint**: `GET /verify`

### Parameters
Pass the two image URLs as query parameters:
* `url1` (string, required): The URL of the first picture.
* `url2` (string, required): The URL of the second picture.

### Example Request
```http
GET https://your-railway-app-domain.up.railway.app/verify?url1=https://example.com/photoA.jpg&url2=https://example.com/photoB.jpg
```

---

## Responses

### 1. Success Match (Status: `200 OK`)
If the deeply analyzed faces match perfectly (even if one is mirrored):
```json
{
  "status": "match",
  "message": "Faces match successfully.",
  "hash": "b5a796bc9d1...", 
  "distance": 0.3541
}
```
* **hash**: A unique SHA-256 identifier generated from the match parameters, which you can use for validation records.

### 2. Mismatch Failure (Status: `403 Forbidden`)
If the faces belong to different people:
```json
{
  "detail": "Faces do not match."
}
```

### 3. Face Detection Failure (Status: `400 Bad Request`)
If a face cannot be clearly found in one or both of the pictures:
```json
{
  "detail": "Face could not be detected in one or both images."
}
```
