import requests
import logging
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class _Session:
    def __init__(self, url, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the scraper session with configurable timeout and retry settings.

        Args:
            url (str): The URL to scrape.
            timeout (int): Request timeout in seconds. Defaults to 30.
            max_retries (int): Maximum number of retry attempts for failed requests. Defaults to 3.
        """
        self.timeout = timeout
        self.session = self._create_session(max_retries)

        # Set custom headers for the session to mimic a legitimate browser request
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Configure logging to capture request errors and other information
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Parse the initial HTML page using BeautifulSoup
        self.soup = self._get_soup(url)

    @staticmethod
    def _create_session(max_retries: int) -> requests.Session:
        """
        Create a configured session object with retry strategy to handle failed requests.

        Args:
            max_retries (int): Maximum retry attempts for failed HTTP requests.

        Returns:
            requests.Session: A session object with attached retry policy.
        """
        session = requests.Session()

        # Define a retry strategy for handling specific HTTP error statuses
        retry_strategy = Retry(
            total=max_retries,  # Total retry attempts
            backoff_factor=1,  # Delay factor between retries
            status_forcelist=[429, 500, 502, 503, 504]  # HTTP status codes to trigger retry
        )

        # Apply the retry strategy to the session's HTTP adapter for HTTP and HTTPS protocols
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_soup(self, url: str):
        """
        Fetch and parse HTML content from a URL.

        Args:
            url (str): The target URL to retrieve and parse.

        Returns:
            BeautifulSoup or None: Parsed HTML content as BeautifulSoup object, or None if an error occurs.
        """
        try:
            # Perform a GET request with specified headers and timeout
            response = self.session.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )

            # Raise an HTTPError if the request returned an unsuccessful status code
            response.raise_for_status()

            # Parse the response text as HTML using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup

        except requests.exceptions.RequestException as e:
            # Log any exceptions encountered during the request
            self.logger.error(e)
            return None
