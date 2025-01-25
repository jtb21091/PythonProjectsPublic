import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class TextGenerationApp:
    def __init__(self, model_name="gpt2"):
        """
        Initialize the text generation app with a specified model.
        
        Args:
            model_name (str): Hugging Face model identifier. Defaults to GPT-2.
        """
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        
        # Set pad token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def generate_text(self, prompt, max_length=100, temperature=0.7):
        """
        Generate text based on the given prompt.
        
        Args:
            prompt (str): Initial text to start generation
            max_length (int): Maximum length of generated text
            temperature (float): Controls randomness of prediction
        
        Returns:
            str: Generated text
        """
        # Encode the input prompt
        input_ids = self.tokenizer.encode(prompt, return_tensors='pt')
        
        # Generate text
        output = self.model.generate(
            input_ids, 
            max_length=max_length, 
            num_return_sequences=1,
            temperature=temperature,
            do_sample=True
        )
        
        # Decode and return generated text
        return self.tokenizer.decode(output[0], skip_special_tokens=True)
    
    def interactive_mode(self):
        """
        Run an interactive text generation session.
        """
        print("Hugging Face Text Generation App")
        print("Type 'quit' to exit.")
        
        while True:
            prompt = input("\nEnter a prompt (or 'quit'): ")
            
            if prompt.lower() == 'quit':
                break
            
            try:
                generated_text = self.generate_text(prompt)
                print("\nGenerated Text:")
                print(generated_text)
            except Exception as e:
                print(f"An error occurred: {e}")

def main():
    # Create and run the app
    app = TextGenerationApp()
    app.interactive_mode()

if __name__ == "__main__":
    main()
