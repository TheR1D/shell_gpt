import unittest
import requests_mock
import requests
from sgpt import ChatGPT


class TestMain(unittest.TestCase):
    API_URL = ChatGPT.API_URL

    def setUp(self):
        self.prompt = "What is the capital of France?"
        self.shell = False
        self.execute = False
        self.code = False
        self.animation = True
        self.spinner = True
        self.api_key = "test-api-key"
        self.temperature = 1.0
        self.top_p = 1.0
        self.response_text = "Paris"
        self.model = "gpt-3.5-turbo"
        self.chat_gpt = ChatGPT(self.api_key)

    @requests_mock.Mocker()
    def test_openai_request(self, mock):
        mocked_json = {"choices": [{"message": {"content": self.response_text}}]}
        mock.post(self.API_URL, json=mocked_json, status_code=200)
        result = self.chat_gpt.get_completion(
            self.prompt, self.model, self.temperature, self.top_p, caching=False
        )
        self.assertEqual(result, self.response_text)
        expected_json = {
            "messages": [{"role": "user", "content": self.prompt}],
            "model": "gpt-3.5-turbo",
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
        expected_headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        request = mock.request_history[0]
        self.assertEqual(request.json(), expected_json)
        for key, value in expected_headers.items():
            self.assertEqual(request.headers[key], value)

    @requests_mock.Mocker()
    def test_openai_request_fail(self, mock):
        mock.post(self.API_URL, status_code=400)
        with self.assertRaises(requests.exceptions.HTTPError):
            self.chat_gpt.get_completion(
                self.prompt, self.model, self.temperature, self.top_p, caching=False
            )


if __name__ == "__main__":
    unittest.main()
