import os
import unittest

import requests
import requests_mock

from sgpt.client import OpenAIClient


class TestMain(unittest.TestCase):
    API_HOST = os.getenv("OPENAI_HOST", "https://api.openai.com")
    API_URL = f"{API_HOST}/v1/chat/completions"
    # TODO: Fix tests.

    def setUp(self):
        self.api_key = os.environ["OPENAI_API_KEY"] = "test key"
        self.prompt = "What is the capital of France?"
        self.shell = False
        self.execute = False
        self.code = False
        self.animation = True
        self.spinner = True
        self.temperature = 1.0
        self.top_p = 1.0
        self.response_text = "Paris"
        self.model = "gpt-3.5-turbo"
        self.client = OpenAIClient(self.API_HOST, self.api_key)

    @requests_mock.Mocker()
    def test_openai_request(self, mock):
        # TODO: Fix tests.
        mocked_json = {"choices": [{"message": {"content": self.response_text}}]}
        mock.post(self.API_URL, json=mocked_json, status_code=200)
        result = yield from self.client.get_completion(
            messages=[{"role": "user", "content": self.prompt}],
            model=self.model,
            temperature=self.temperature,
            top_probability=self.top_p,
            caching=False,
        )
        # TODO: Fix tests with generators.
        self.assertEqual(result, self.response_text)
        expected_json = {
            "messages": [{"role": "user", "content": self.prompt}],
            "model": "gpt-3.5-turbo",
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
        expected_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        request = mock.request_history[0]
        self.assertEqual(request.json(), expected_json)
        for key, value in expected_headers.items():
            self.assertEqual(request.headers[key], value)

    @requests_mock.Mocker()
    def test_openai_request_fail(self, mock):
        # TODO: Fix tests.
        mock.post(self.API_URL, status_code=400)
        with self.assertRaises(requests.exceptions.HTTPError):
            yield from self.client.get_completion(
                messages=[{"role": "user", "content": self.prompt}],
                model=self.model,
                temperature=self.temperature,
                top_probability=self.top_p,
                caching=False,
            )


if __name__ == "__main__":
    unittest.main()
