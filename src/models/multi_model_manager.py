# src/models/multi_model_manager.py

class MultiModelManager:
    def __init__(self):
        self.models = {}

    def load_model(self, model_name, model_path):
        """
        Loads a model into the manager.
        """
        print(f"Loading model: {model_name} from {model_path}")
        # Placeholder for actual model loading logic
        self.models[model_name] = {"path": model_path, "status": "loaded"}
        return True

    def unload_model(self, model_name):
        """
        Unloads a model from the manager.
        """
        if model_name in self.models:
            print(f"Unloading model: {model_name}")
            del self.models[model_name]
            return True
        return False

    def get_model(self, model_name):
        """
        Retrieves a loaded model.
        """
        return self.models.get(model_name)

    def list_loaded_models(self):
        """
        Lists all currently loaded models.
        """
        return list(self.models.keys())

# Example Usage (for testing purposes)
if __name__ == "__main__":
    manager = MultiModelManager()
    manager.load_model("model_a", "/path/to/model_a")
    manager.load_model("model_b", "/path/to/model_b")
    print("Loaded models:", manager.list_loaded_models())
    print("Getting model_a:", manager.get_model("model_a"))
    manager.unload_model("model_a")
    print("Loaded models after unload:", manager.list_loaded_models())
