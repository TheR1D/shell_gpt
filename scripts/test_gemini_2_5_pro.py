# This script tests accessing the Gemini 2.5 Pro model via the Vertex AI SDK.
# Based on the information and example provided by the user.

from google.cloud import aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel # Part is not used in the example directly for generate_content

def test_gemini_model():
    """
    Initializes Vertex AI, loads a Gemini model, and attempts to generate content.
    """
    project_id = "gen-lang-client-0548749131"
    location = "us-east1" # Changed region to us-east1 for testing
    # As per user's information, this is the model ID to test.
    # IMPORTANT: Verify this is the correct and available model identifier string
    # from the official Google Cloud Vertex AI documentation.
    model_id_for_api = "gemini-2.0-flash-001" # Changed to user-provided stable version

    print(f"Initializing Vertex AI for project '{project_id}' in location '{location}'...")
    try:
        vertexai.init(project=project_id, location=location)
        print("Vertex AI initialized successfully.")
    except Exception as e:
        print(f"Error initializing Vertex AI: {e}")
        return

    print(f"Attempting to load model: '{model_id_for_api}'...")
    try:
        model = GenerativeModel(model_id_for_api)
        print(f"Model '{model_id_for_api}' loaded successfully.")
    except Exception as e:
        print(f"Error loading model '{model_id_for_api}': {e}")
        print("Please ensure the model ID is correct and the model is available in your region/project.")
        print("Refer to the official Google Cloud Vertex AI documentation for available models and their identifiers.")
        return

    prompt = "Tell me a short fun fact about Large Language Models."
    print(f"\nGenerating content with prompt: \"{prompt}\"")

    try:
        response = model.generate_content(prompt)
        print("\nResponse from model:")
        # Check if response has 'text' attribute, Gemini API can have complex response structures
        if hasattr(response, 'text'):
            print(response.text)
        else:
            # Fallback for potentially more complex response objects
            # (e.g. if streaming or multi-part)
            print(str(response))
            print("(Response object might not have a direct '.text' attribute, printed full response)")

    except Exception as e:
        print(f"\nAn error occurred during content generation: {e}")
        print("This could be due to various reasons including permissions, model issues, or quota limits.")

if __name__ == "__main__":
    test_gemini_model()