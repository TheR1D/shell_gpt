import unittest
import requests_mock
import requests
import sgpt


class TestMain(unittest.TestCase):
    def setUp(self):
        self.prompt = "What is the capital of France?"
        self.model = "text-davinci-003"
        self.max_tokens = 2048
        self.shell = False
        self.execute = False
        self.code = False
        self.animation = True
        self.spinner = True
        self.api_key = "test-api-key"
        self.temperature = 1.0
        self.top_p = 1.0
        self.response_text = "Paris"

    @requests_mock.Mocker()
    def test_openai_request(self, mock):
        mock.post(sgpt.API_URL, json={"choices": [{"text": self.response_text}]}, status_code=200)
        result = sgpt.openai_request(
            self.prompt, self.model, self.max_tokens, self.api_key, self.temperature, self.top_p, spinner=self.spinner
        )
        self.assertEqual(result, self.response_text)
        expected_json = {
            "prompt": self.prompt,
            "model": self.model,
            "max_tokens": self.max_tokens,
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
        mock.post(sgpt.API_URL, status_code=400)
        with self.assertRaises(requests.exceptions.HTTPError):
            sgpt.openai_request(
                self.prompt,
                self.model,
                self.max_tokens,
                self.api_key,
                self.temperature,
                self.top_p,
                spinner=self.spinner,
            )


if __name__ == "__main__":
    unittest.main()
