# src/test_llm.py

from llama_cpp import Llama
import os
import time
import gc # For garbage collection

# --- Global Configuration ---
MODEL_FILENAME = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
INPUT_TEXT_FILENAME = "clase_gestion.txt" # File from data/ directory

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, "..", "models", MODEL_FILENAME)
INPUT_TEXT_FILE_PATH = os.path.join(SCRIPT_DIR, "..", "data", INPUT_TEXT_FILENAME)

CONTEXT_SIZE = 8192  # Context window size
TOKENS_FOR_TEST_GENERATION = 4096 # Max tokens to generate for the test summary

def run_single_test_configuration(config_name: str, model_load_params: dict, full_prompt: str, tokens_to_generate: int):
    """
    Runs a single performance test with a given model configuration and prompt.
    """
    print(f"\n--- Running Test Configuration: {config_name} ---")
    print(f"Model Load Parameters: {model_load_params}")

    llm = None
    try:
        # Add main_gpu setting if n_gpu_layers > 0
        if model_load_params.get("n_gpu_layers", 0) > 0:
            model_load_params_updated = {**model_load_params, "main_gpu": 0, "verbose": False}
            print("Explicitly setting main_gpu=0 for GPU offload.")
        else:
            model_load_params_updated = {**model_load_params, "verbose": False}

        # Load the model
        load_start_time = time.time()
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=CONTEXT_SIZE,
            **model_load_params_updated
        )
        load_end_time = time.time()
        load_duration = load_end_time - load_start_time
        print(f"Model loaded in {load_duration:.2f} seconds.")

        # Perform inference
        print(f"Prompting with {len(full_prompt)} characters...")
        inference_start_time = time.time()
        output = llm(
            full_prompt,
            max_tokens=tokens_to_generate,
            stop=None, # Let it generate up to max_tokens or naturally stop
            echo=False
        )
        inference_end_time = time.time()
        inference_duration = inference_end_time - inference_start_time

        generated_text = output['choices'][0]['text'].strip()
        prompt_tokens_count = output['usage']['prompt_tokens']
        generated_tokens_count = output['usage']['completion_tokens']
        
        tokens_per_second = 0
        if inference_duration > 0 and generated_tokens_count > 0:
            tokens_per_second = generated_tokens_count / inference_duration

        print(f"Inference completed in {inference_duration:.2f} seconds.")
        print(f"Prompt tokens: {prompt_tokens_count}")
        print(f"Generated tokens: {generated_tokens_count}")
        print(f"Tokens per second: {tokens_per_second:.2f}")
        print(f"Generated text (first 100 chars):\n'{generated_text[:100]}...'")
        print("")
        print("")
        print("")
        print("")
        print(f"SALIDA COMPLETA DEL LLM: {output}")

    except Exception as e:
        print(f"ERROR during test '{config_name}': {e}")
        print("Possible causes:")
        print("- Ensure 'llama-cpp-python' is correctly installed (with C++ build tools).")
        print("- Verify MODEL_PATH is correct and the model file exists.")
        print("- Insufficient RAM/VRAM for the current configuration (try reducing n_gpu_layers or using a smaller model).")
        print("- Corrupted model file.")
    finally:
        if llm is not None:
            del llm # Release the model
        gc.collect() # Explicitly run garbage collection
        print("--- Test Configuration Finished ---")


def main():
    print("Starting LLM Performance Test Suite...")

    # Check if model file exists
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model file not found at {MODEL_PATH}")
        print("Please ensure MODEL_FILENAME is correct and the model is in the 'models' directory.")
        return

    # Check if input text file exists
    if not os.path.exists(INPUT_TEXT_FILE_PATH):
        print(f"ERROR: Input text file not found at {INPUT_TEXT_FILE_PATH}")
        print(f"Please ensure {INPUT_TEXT_FILENAME} is in the 'data' directory.")
        return

    # Read input text
    try:
        with open(INPUT_TEXT_FILE_PATH, "r", encoding="utf-8") as f:
            text_content = f.read()
        print(f"Successfully read input text from {INPUT_TEXT_FILENAME} ({len(text_content)} characters).")
    except Exception as e:
        print(f"Error reading input text file: {e}")
        return

    # Define the prompt using the input text
    # You can customize this prompt for different tasks
    prompt_template = "Analiza el siguiente texto y genera un ensayo sobre lo que trata el texto:\n\n{TEXT_CONTENT}"
    test_prompt = prompt_template.format(TEXT_CONTENT=text_content)

    # --- Define Test Configurations ---
    # (n_gpu_layers, n_threads, n_batch)
    # n_threads=None lets llama.cpp choose an optimal number.
    # For your E4s_v4 VM (4 vCPUs), testing with n_threads=4 is a good idea.
    configurations = [
        # CPU Tests
        # ("CPU_default_threads_batch512", {"n_gpu_layers": 0, "n_threads": None, "n_batch": 512}),
        # ("CPU_4_threads_batch512",       {"n_gpu_layers": 0, "n_threads": 4,    "n_batch": 512}),
        # ("CPU_4_threads_batch256",       {"n_gpu_layers": 0, "n_threads": 4,    "n_batch": 256}),
        
        # GPU Offload Tests (adjust n_gpu_layers based on your VM's capabilities and model size)
        # For a 7B Q4_K_M model (~4-5GB) and 32GB RAM, you can experiment with these.
        # On a CPU-only VM, n_gpu_layers > 0 will still use RAM as if it were VRAM.
        # ("GPU_10_layers_batch512",       {"n_gpu_layers": 10, "n_threads": None, "n_batch": 512}),
        # ("GPU_10_layers_4_threads_batch512", {"n_gpu_layers": 10, "n_threads": 4, "n_batch": 512}),
        # ("GPU_20_layers_batch512",       {"n_gpu_layers": 10, "n_threads": None, "n_batch": 256}), # Potentially heavy
        ("GPU_20_layers_batch512",       {"n_gpu_layers": 20, "n_threads": 4, "n_batch": 256}),
        # ("GPU_20_layers_batch512",       {"n_gpu_layers": 20, "n_threads": None, "n_batch": 512}),
        # # ("GPU_20_layers_batch512",       {"n_gpu_layers": 20, "n_threads": 4, "n_batch": 512}),
        # ("GPU_20_layers_batch512",       {"n_gpu_layers": 20, "n_threads": None, "n_batch": 256}),
        # ("GPU_20_layers_batch512",       {"n_gpu_layers": 20, "n_threads": 4, "n_batch": 256}),
        # ("GPU_20_layers_batch512",       {"n_gpu_layers": -1, "n_threads": None, "n_batch": 256}),
        ("GPU_20_layers_batch512",       {"n_gpu_layers": -1, "n_threads": None, "n_batch": 512})
    ]

    for name, params in configurations:
        run_single_test_configuration(
            config_name=name,
            model_load_params=params,
            full_prompt=test_prompt,
            tokens_to_generate=TOKENS_FOR_TEST_GENERATION
        )

    print("\nAll performance tests completed.")

if __name__ == "__main__":
    main()