import concurrent.futures
import os
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup
from instructor import OpenAISchema
from pydantic import Field

from sgpt.config import cfg


# Note: This tool requires full testing and proper configuration before production use.
# Required environment variables must be set for this tool to function correctly.
# TODO: More adapter is required(sorry for I didn't finished it).
class Function(OpenAISchema):
    """
    Performs an internet search using Google Custom Search API and returns the results.
    """

    query: str = Field(
        ...,
        example="latest developments in artificial intelligence",
        description="The search query to look up on the internet.",
    )

    num_results: int = Field(
        default=5,
        ge=1,
        le=10,
        example=5,
        description="Number of search results to return, between 1 and 10.",
    )

    class Config:
        title = "internet_search"

    @classmethod
    def _get_search_config(cls):
        """Get search configuration"""
        # Environment variables must be set for this tool to work properly
        return {
            "INTERNET_SEARCH_ENGINE_API": os.getenv(
                "INTERNET_SEARCH_ENGINE_API",
                "https://www.googleapis.com/customsearch/v1",
            ),
            "INTERNET_SEARCH_API_KEY": os.getenv("INTERNET_SEARCH_API_KEY", None),
            "INTERNET_SEARCH_API_CX": os.getenv("INTERNET_SEARCH_API_CX", None),
        }

    @classmethod
    def _googleapis(cls, query: str, num: int) -> List[Tuple[str, str]]:
        """
        Perform search using Google Custom Search API

        Args:
            query: Search keywords
            num: Number of results to return

        Returns:
            list[tuple[str, str]]: [(title, link), ...]

        Raises:
            ValueError: When API key or CX is not configured
            requests.exceptions.RequestException: Network request exception
            KeyError: API response format exception
        """
        SEARCH_CONFIG = cls._get_search_config()

        # Check required configurations
        if not SEARCH_CONFIG["INTERNET_SEARCH_API_KEY"]:
            raise ValueError("Google Search API key is not configured")

        if not SEARCH_CONFIG["INTERNET_SEARCH_API_CX"]:
            raise ValueError("Google Search API CX is not configured")

        url = SEARCH_CONFIG["INTERNET_SEARCH_ENGINE_API"]
        params = {
            "q": query,
            "num": num,
            "safe": "off",
            "key": SEARCH_CONFIG["INTERNET_SEARCH_API_KEY"],
            "cx": SEARCH_CONFIG["INTERNET_SEARCH_API_CX"],
        }

        try:
            # set request timeout
            timeout = int(cfg.get("REQUEST_TIMEOUT"))
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            # Check if API returns an error
            if "error" in data:
                error_msg = data["error"].get("message", "Unknown API error")
                raise requests.exceptions.RequestException(
                    f"Google API error: {error_msg}"
                )

            results = []
            items = data.get("items", [])

            for item in items:
                title = item.get("title", "")
                link = item.get("link", "")
                if title and link:
                    results.append((title, link))

            return results

        except requests.exceptions.Timeout as e:
            raise requests.exceptions.Timeout(
                "Google Search API request timeout"
            ) from e
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Request failed: {str(e)}"
            ) from e
        except ValueError as e:
            # JSON parsing error
            raise requests.exceptions.RequestException(
                f"Failed to parse API response: {str(e)}"
            ) from e

    @classmethod
    def _fetch_and_process_web_content(cls, search_results: list) -> List[Tuple[str, str]]:
        """
        Sequentially visit URLs in search results, fetch web page content and process it

        Args:
            search_results: [(title, url), ...] list returned by googleapis function

        Returns:
            list[tuple[str, str]]: [(title, processed content), ...]
        """
        processed_content = []

        # Set request timeout
        timeout = int(cfg.get("REQUEST_TIMEOUT"))

        # Use ThreadPoolExecutor to fetch web content concurrently
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(10, len(search_results))
        ) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(cls._fetch_single_page, title, url, timeout): (
                    title,
                    url,
                )
                for title, url in search_results
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                title, url = future_to_url[future]
                try:
                    content = future.result()
                    processed_content.append((title, content))
                except Exception as e:
                    # If fetching webpage fails, add error message
                    processed_content.append(
                        (title, f"Failed to fetch content: {str(e)}")
                    )

        return processed_content

    @classmethod
    def _fetch_single_page(cls, title: str, url: str, timeout: int) -> str:
        """
        Fetch and process content from a single URL

        Args:
            title: Page title
            url: Page URL
            timeout: Request timeout in seconds

        Returns:
            str: Processed content
        """
        # Set request headers to simulate browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.decompose()

        # Try to get main content area
        # Prioritize searching for content-related tags
        content_selectors = [
            "main",
            "article",
            '[role="main"]',
            ".content",
            "#content",
            ".post",
            ".article",
            "body",
        ]

        text_content = ""
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                text_content = content_element.get_text(separator=" ", strip=True)
                break

        if not text_content:
            # If no specific content area is found, get text from entire body
            body = soup.find("body")
            if body:
                text_content = body.get_text(separator=" ", strip=True)
            else:
                text_content = soup.get_text(separator=" ", strip=True)

        # Clean text content
        # Remove extra whitespace characters and line breaks
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = " ".join(chunk for chunk in chunks if chunk)

        # Limit content length to avoid excessive length
        if len(text_content) > 4096:
            text_content = text_content[:4096] + "..."

        return text_content

    @classmethod
    def _convert_to_readable_string(cls, processed_content: List[Tuple[str, str]]) -> str:
        """
        Convert processed content to a readable long string

        Args:
            processed_content: [(title, content), ...] list

        Returns:
            str: Formatted long string
        """
        result_parts = []

        for i, (title, content) in enumerate(processed_content, 1):
            section = f"=== No.{i} result ===\n"
            section += f"Title: {title}\n"
            section += f"Content: {content}\n"
            section += "=" * 50 + "\n"
            result_parts.append(section)

        return "\n".join(result_parts)

    @classmethod
    def execute(cls, query: str, num_results: int = 5) -> str:
        """
        Execute the internet search tool

        Args:
            query: The search query
            num_results: Number of results to return (1-10)

        Returns:
            str: Formatted search results
        """
        try:
            # Perform search
            search_results = cls._googleapis(query, num_results)

            if not search_results:
                return "Exit code: 0, Output:\nNo search results were found for your query."

            # Fetch web content
            processed_content = cls._fetch_and_process_web_content(search_results)

            # Convert to readable format
            readable_output = cls._convert_to_readable_string(processed_content)

            return f"Exit code: 0, Output:\n{readable_output}"

        except ValueError as e:
            return (
                "Exit code: 1, Output:\nInternet search tool configuration error: "
                + str(e)
                + ". Please check your API key and search engine configuration."
            )
        except requests.exceptions.Timeout as e:
            return (
                "Exit code: 1, Output:\nSearch request timed out after "
                + str(cfg.get("REQUEST_TIMEOUT"))
                + " seconds. Error details: "
                + str(e)
                + ". Please try a different query or check your network connection."
            )
        except requests.exceptions.RequestException as e:
            return (
                "Exit code: 1, Output:\nNetwork error during search. Error details: "
                + str(e)
                + ". Please check your network connection and API configuration."
            )
        except Exception as e:
            return (
                "Exit code: 1, Output:\nUnexpected error during search. Error type: "
                + type(e).__name__
                + ", Error details: "
                + str(e)
                + ". The operation has been terminated to prevent further issues."
            )
