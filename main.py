import os
import gc
import urllib.request
import numpy as np
import cv2
from fastapi import FastAPI, HTTPException, Query
from deepface import DeepFace
import hashlib

app = FastAPI(title="Face Verification API (Memory Only)")

# Pre-load DeepFace weights (ArcFace, retinaface)
try:
    print("Pre-loading DeepFace weights (ArcFace, retinaface)...")
    DeepFace.build_model("ArcFace")
    DeepFace.build_model("retinaface")
except Exception as e:
    print(f"Pre-load notice: {e}")

def download_image_to_memory(url: str) -> np.ndarray:
    """Download an image from a URL directly into a numpy array (in-memory)."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            image_data = response.read()
            # Convert binary data to numpy array
            image_array = np.asarray(bytearray(image_data), dtype=np.uint8)
            # Decode the numpy array to OpenCV image (BGR format)
            img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Could not decode image.")
            return img
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch/decode image from {url}: {str(e)}")

def process_verification(img1: np.ndarray, img2: np.ndarray):
    """Run verification between two in-memory images."""
    try:
        # DeepFace can accept numpy arrays directly (BGR format from OpenCV)
        result = DeepFace.verify(
            img1_path=img1, 
            img2_path=img2,
            model_name="ArcFace",
            detector_backend="retinaface",
            enforce_detection=True
        )
        return result
    except ValueError as val_err:
        if "Face could not be detected" in str(val_err):
            raise ValueError("Face could not be detected in one or both images.")
        raise
    except Exception as e:
        raise RuntimeError(f"DeepFace verification failed: {str(e)}")


@app.get("/verify")
def verify_faces(url1: str = Query(...), url2: str = Query(...)):
    if not url1 or not url2:
        raise HTTPException(status_code=400, detail="url1 and url2 query parameters are required.")
    
    # Download images strictly to memory (RAM)
    img1 = download_image_to_memory(url1)
    img2 = download_image_to_memory(url2)
    
    try:
        # 1. First attempt: Direct verification
        try:
            result = process_verification(img1, img2)
            is_match = result["verified"]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
             raise HTTPException(status_code=500, detail=str(e))

        # 2. If it's not a match, attempt to flip the second image
        if not is_match:
            try:
                # Flip img2 horizontally (in-memory)
                img2_flipped = cv2.flip(img2, 1) 
                
                # Try verifying with the flipped image
                flipped_result = process_verification(img1, img2_flipped)
                
                if flipped_result["verified"]:
                    is_match = True
                    result = flipped_result
            except Exception as e:
                print(f"Error during flipped verification fallback: {e}")
                pass
        
        # 3. Final Evaluation
        if is_match:
            # Create unique match hash
            raw_hash_string = f"{url1}|{url2}|{result.get('distance', 0)}".encode('utf-8')
            match_hash = hashlib.sha256(raw_hash_string).hexdigest()
            
            return {
                "status": "match",
                "message": "Faces match successfully.",
                "hash": match_hash,
                "distance": result.get("distance")
            }
        else:
            raise HTTPException(status_code=403, detail="Faces do not match.")
            
    finally:
        # Explicitly delete the image variables from memory
        del img1
        del img2
        
        # Force garbage collection immediately to clear RAM cache
        gc.collect()

if __name__ == "__main__":
    import uvicorn
    # Use PORT env variable if available (for Railway)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
