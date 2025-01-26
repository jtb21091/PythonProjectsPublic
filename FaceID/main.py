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

    def capture_face_embedding(self):
        """Capture face embedding using Dlib from the webcam."""
        print("Accessing webcam. Press 's' to save or 'q' to quit.")
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            raise Exception("Could not access the webcam.")

        embedding = None

        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break

            # Convert to grayscale for Dlib
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.detector(gray)

            # Highlight detected face(s) in the webcam feed
            for face in faces:
                x, y, w, h = (face.left(), face.top(), face.width(), face.height())
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            cv2.imshow("Webcam Face Capture - Press 's' to Save or 'q' to Quit", frame)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s') and len(faces) > 0:  # Save the face embedding if 's' is pressed
                face = faces[0]
                shape = self.shape_predictor(gray, face)
                embedding = np.array(self.face_recognizer.compute_face_descriptor(frame, shape))
                print("Face embedding captured.")
                break
            elif key == ord('q'):  # Quit without saving
                print("Exiting webcam without capturing face.")
                break

        cap.release()
        cv2.destroyAllWindows()

        if embedding is None:
            raise ValueError("No face embedding was captured. Please try again.")

        return embedding

    def encrypt_data(self, data):
        """Encrypt data using Fernet symmetric encryption."""
        metadata = f"{data.dtype}:{data.shape}".encode()
        print("Metadata for encryption:", metadata)  # Debug
        data_bytes = data.tobytes()
        combined_data = metadata + b"||" + data_bytes
        print("Combined Data Before Encryption:", combined_data[:100])  # Debug
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
        print("Encrypted Data Loaded:", encrypted_data[:100])  # Debug

        decrypted_data = fernet.decrypt(encrypted_data)
        print("Decrypted Data:", decrypted_data[:100])  # Debug

        if b"||" not in decrypted_data:
            raise ValueError("Decrypted data is improperly formatted. '||' delimiter is missing.")
        
        metadata, data_bytes = decrypted_data.split(b"||", 1)
        print("Metadata:", metadata)  # Debug

        try:
            dtype, shape = metadata.decode().split(":")
            print("Parsed dtype:", dtype)  # Debug
            print("Parsed shape (raw):", shape)  # Debug
            shape = eval(shape)  # Convert string "(128,)" into a Python tuple
            print("Parsed shape (evaluated):", shape)  # Debug
        except Exception as e:
            raise ValueError(f"Metadata parsing failed. Metadata: {metadata}, Error: {e}")

        return np.frombuffer(data_bytes, dtype=dtype).reshape(shape)

    def compare_embeddings(self, embedding1, embedding2, threshold=0.6):
        """Compare two embeddings using Euclidean distance."""
        distance = np.linalg.norm(embedding1 - embedding2)
        print(f"Calculated Distance: {distance}")
        return distance < threshold


# Main Section
if __name__ == "__main__":
    face_recognition = SecureFaceRecognition()

    try:
        if os.path.exists("face_data.enc"):
            stored_embedding = face_recognition.load_and_decrypt("face_data.enc")
            print("Stored Face Embedding Loaded.")
        else:
            print("No stored face data found. Please capture your face embedding first.")
            new_embedding = face_recognition.capture_face_embedding()
            face_recognition.save_securely(new_embedding, "face_data.enc")
            print("Face embedding saved securely.")
            exit(0)

        new_embedding = face_recognition.capture_face_embedding()
        is_match = face_recognition.compare_embeddings(stored_embedding, new_embedding)
        print("Face recognized!" if is_match else "Face not recognized.")
    except Exception as e:
        print("Error:", e)
