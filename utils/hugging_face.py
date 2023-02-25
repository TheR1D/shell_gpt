import requests

models = {
    "sentence_translation": "https://api-inference.huggingface.co/models/sentence-transformers/paraphrase-MiniLM-L6-v2",
    "naming": "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
}

def hugging_face_api(request_data, model, api_key):
    response = requests.post(
        models[model], 
        headers={"Authorization": f"Bearer {api_key}"}, 
        json=request_data
    )
    return response.json()
