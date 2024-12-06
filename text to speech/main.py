import pyttsx3

# Initialize the text-to-speech engine
try:
    engine = pyttsx3.init()  # Default driver should work on macOS
except Exception as e:
    print(f"Error initializing pyttsx3: {e}")
    exit(1)

# Set properties
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)

# Define the text to be spoken
text = "Hello, Joshua! This is a test of the text-to-speech functionality."

# Perform the speech
try:
    engine.say(text)
    engine.runAndWait()
except Exception as e:
    print(f"Error during text-to-speech: {e}")
    exit(1)
