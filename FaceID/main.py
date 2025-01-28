import cv2
import dlib
import numpy as np
from cryptography.fernet import Fernet
import os
import urllib.request
import bz2
import shutil


class SecureFaceRecognition:
    def __init__(self):
        # Load or generate the encryption key
        self.key_file = "encryption_key.key"
        if not os.path.exists(self.key_file):
            self.generate_key()
        self.key = self.load_key()

        # Paths to pre-trained Dlib models
        self.shape_predictor_path = "shape_predictor_68_face_landmarks.dat"
        self.face_recognition_model_path = "dlib_face_recognition_resnet_model_v1.dat"

        # Ensure the model files exist, or download them
        self.download_dlib_model(
            "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2",
            self.shape_predictor_path,
        )
        self.download_dlib_model(
            "http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2",
            self.face_recognition_model_path,
        )

        # Dlib face detector, shape predictor, and face recognizer
        self.detector = dlib.get_frontal_face_detector()
        self.shape_predictor = dlib.shape_predictor(self.shape_predictor_path)
        self.face_recognizer = dlib.face_recognition_model_v1(self.face_recognition_model_path)

    def generate_key(self):
        """Generate a new encryption key and save to a file."""
        key = Fernet.generate_key()
        with open(self.key_file, "wb") as key_file:
            key_file.write(key)
        print("Encryption key generated and saved.")

    def load_key(self):
        """Load the encryption key from the file."""
        with open(self.key_file, "rb") as key_file:
            return key_file.read()

    def download_dlib_model(self, url, output_path):
        """Download and extract Dlib models if not already present."""
        if not os.path.exists(output_path):
            print(f"Downloading {url}...")
            compressed_file = output_path + ".bz2"
            urllib.request.urlretrieve(url, compressed_file)
            print(f"Extracting {compressed_file}...")
            with bz2.BZ2File(compressed_file, "rb") as file, open(output_path, "wb") as out_file:
                shutil.copyfileobj(file, out_file)
            os.remove(compressed_file)
            print(f"Model {output_path} ready for use.")

    def capture_face_embedding(self, live_mode=False, stored_embedding=None):
        """Capture face embedding using Dlib from the webcam and save the image."""
        print("Accessing webcam. Ensure proper lighting and position your face in the center.")
        print("Press 's' to save a picture and face embedding or 'q' to quit.")
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            raise Exception("Could not access the webcam.")

        embedding = None
        captured_image = None

        try:
            while True:
                # Capture frame-by-frame
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame.")
                    break

                # Convert to grayscale for Dlib processing
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.detector(gray)

                # Draw rectangles around detected faces
                for face in faces:
                    x, y, w, h = (face.left(), face.top(), face.width(), face.height())
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # If in live mode, compare with stored embedding
                    if live_mode and stored_embedding is not None:
                        shape = self.shape_predictor(gray, face)
                        live_embedding = np.array(self.face_recognizer.compute_face_descriptor(frame, shape))
                        distance = np.linalg.norm(stored_embedding - live_embedding)

                        if distance < 0.6:
                            label = f"Recognized (Dist: {distance:.2f})"
                        else:
                            label = f"Not Recognized (Dist: {distance:.2f})"

                        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if distance < 0.6 else (0, 0, 255), 2)

                cv2.imshow("Webcam Face Capture - Press 's' to Save or 'q' to Quit", frame)

                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('s') and len(faces) > 0:  # Save the face embedding and image
                    face = faces[0]
                    shape = self.shape_predictor(gray, face)
                    embedding = np.array(self.face_recognizer.compute_face_descriptor(frame, shape))
                    captured_image = frame.copy()
                    print("Face embedding and image captured successfully.")
                    break
                elif key == ord('q'):  # Quit without saving
                    print("Exiting webcam without capturing face.")
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()

        if embedding is None and not live_mode:
            raise ValueError("No face embedding or image was captured. Please position your face correctly and try again.")

        if not live_mode and captured_image is not None:
            # Save the captured image
            image_file_name = "captured_face.jpg"
            cv2.imwrite(image_file_name, captured_image)
            print(f"Captured image saved as {image_file_name}")

        return embedding

    def encrypt_data(self, data):
        """Encrypt data using Fernet symmetric encryption."""
        metadata = f"{data.dtype}:{data.shape}".encode()
        data_bytes = data.tobytes()
        combined_data = metadata + b"||" + data_bytes
        fernet = Fernet(self.key)
        encrypted_data = fernet.encrypt(combined_data)
        return encrypted_data

    def save_securely(self, data, file_name="face_data.enc"):
        """Save encrypted data to a file."""
        encrypted_data = self.encrypt_data(data)
        with open(file_name, "wb") as file:
            file.write(encrypted_data)
        print(f"Encrypted face data saved to {file_name}")

    def load_and_decrypt(self, file_name="face_data.enc"):
        """Load and decrypt face data from a file."""
        fernet = Fernet(self.key)
        with open(file_name, "rb") as file:
            encrypted_data = file.read()

        decrypted_data = fernet.decrypt(encrypted_data)

        if b"||" not in decrypted_data:
            raise ValueError("Decrypted data is improperly formatted. '||' delimiter is missing.")

        metadata, data_bytes = decrypted_data.split(b"||", 1)
        dtype, shape = metadata.decode().split(":")
        shape = eval(shape)  # Convert string to tuple

        return np.frombuffer(data_bytes, dtype=dtype).reshape(shape)

    def compare_embeddings(self, embedding1, embedding2, threshold=0.6):
        """Compare two embeddings using Euclidean distance."""
        distance = np.linalg.norm(embedding1 - embedding2)
        print(f"Calculated Distance: {distance}")  # Debug: show distance
        return distance < threshold


# Main Section
if __name__ == "__main__":
    face_recognition = SecureFaceRecognition()

    try:
        if os.path.exists("face_data.enc"):
            # Load stored embedding
            stored_embedding = face_recognition.load_and_decrypt("face_data.enc")
            print("Stored Face Embedding Loaded.")

            # Live recognition mode
            print("Entering live recognition mode. Position yourself in front of the camera.")
            face_recognition.capture_face_embedding(live_mode=True, stored_embedding=stored_embedding)

        else:
            print("No stored face data found. Please capture your face embedding first.")
            new_embedding = face_recognition.capture_face_embedding()
            face_recognition.save_securely(new_embedding, "face_data.enc")
            print("Face embedding saved securely.")
    except Exception as e:
        print("Error:", e)
