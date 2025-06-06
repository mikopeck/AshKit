# llm_interface.py
import ollama

def query_ollama_model(model_name: str, prompt: str, system_message: str = None) -> str:
    """Queries a specified Ollama model."""
    try:
        messages = []
        if system_message:
            messages.append({'role': 'system', 'content': system_message})
        messages.append({'role': 'user', 'content': prompt})

        response = ollama.chat(
            model=model_name,
            messages=messages
        )
        return response['message']['content']
    except Exception as e:
        # More detailed error logging
        error_message = f"Error querying Ollama model '{model_name}'. Please ensure Ollama is running and the model is downloaded. Details: {str(e)}"
        print(error_message)
        # Re-raise the exception so the calling function knows something went wrong.
        raise ConnectionError(error_message)