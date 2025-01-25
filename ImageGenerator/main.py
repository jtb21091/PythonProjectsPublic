#based on https://github.com/apple/ml-stable-diffusion

import torch
from diffusers import StableDiffusionPipeline
import os

def generate_image(prompt, output_path, model_path="CompVis/stable-diffusion-v1-4", device=None):
    """
    Generates an image based on a text prompt using the ml-stable-diffusion library.

    Args:
        prompt (str): The text prompt to guide image generation.
        output_path (str): Path to save the generated image.
        model_path (str): Path or identifier for the pre-trained model.
        device (str): The device to run the model on (e.g., "cuda", "mps", or "cpu").
    """
    # Automatically set device to "mps" if on Apple Silicon
    if device is None:
        device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    # Load the stable diffusion pipeline
    print(f"Loading the model on {device}...")
    pipeline = StableDiffusionPipeline.from_pretrained(model_path)
    pipeline.to(device)

    # Generate the image
    print(f"Generating image for prompt: {prompt}")
    with torch.no_grad():
        image = pipeline(prompt).images[0]

    # Save the image in the current working directory
    output_path = os.path.join(os.getcwd(), os.path.basename(output_path))
    image.save(output_path)
    print(f"Image saved to {output_path}")

if __name__ == "__main__":
    # Default values for testing in VSCode
    prompt = "A labrador retriever wearing a tuxedo"
    output_path = "test_image.png"
    model_path = "CompVis/stable-diffusion-v1-4"
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    generate_image(prompt, output_path, model_path, device)
