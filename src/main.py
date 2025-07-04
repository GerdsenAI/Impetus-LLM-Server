# src/main.py
from models.multi_model_manager import MultiModelManager

def main():
    print("Starting Impetus-LLM-Server application...")
    manager = MultiModelManager()

    # Example usage of MultiModelManager
    manager.load_model("default_llm", "/path/to/default_llm_model")
    manager.load_model("secondary_model", "/path/to/secondary_model")

    print("\nCurrently loaded models:")
    for model_name in manager.list_loaded_models():
        print(f"- {model_name}")

    # Placeholder for API integration or further application logic
    print("\nApplication ready. (Further API integration and logic to be added)")

if __name__ == "__main__":
    main()
