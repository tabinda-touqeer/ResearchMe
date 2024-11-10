
__all__ = ["Mirror1"]

__author__ = "Tabinda Touqeer"
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2024 Tabinda Touqeer"
# Use of this source code is governed by the MIT license.
__license__ = "MIT"

import re
import logging
import requests


class Mirror1:
    def __init__(self):
        """
        Initializes the Mirror1 object, setting up logging and defining
        session and soup attributes for HTML parsing.
        """
        logging.basicConfig(level=logging.INFO)
        self._logger = logging.getLogger(__name__)
        self._session = None
        self._soup = None

    def _initialize_session(self, url):
        """
        Initializes a session to scrape data from the given URL.

        Args:
            url (str): The URL to be scraped.
        """
        from ._scrapper_sessions import _Session
        try:
            # Create a session and retrieve parsed HTML content (soup)
            self._session = _Session(url)
            self._soup = self._session.soup
            if not self._soup:
                self._logger.error("Failed to initialize soup. Soup is None.")
        except Exception as e:
            # Log any exceptions encountered during session initialization
            self._logger.error(f"Error initializing session for URL {url}: {e}")

    def get_metadata(self, max_entries=100):
        """
        Extracts metadata from the parsed HTML content, including book details.

        Args:
            max_entries (int): Maximum number of entries to return. Defaults to 100.

        Returns:
            list: A list of dictionaries containing metadata for each entry, or None if soup is not initialized.
        """
        if not self._soup:
            self._logger.warning("No soup object available. Please initialize the session first.")
            return None

        tables = self._soup.findAll('table')
        metadata_list = []

        # Check if the page structure includes relevant content tables
        if len(self._soup.findAll('table')) > 2:
            cont_tab = tables[1]
            # Process each row within the content table
            for row in cont_tab.find_all('tr'):
                cells = row.find_all('td')
                if cells:
                    # Extract metadata from each cell
                    img_tag = cells[0].find('img')
                    thumbnail = 'https://libgen.li' + img_tag['src'].replace('_small', '') if img_tag else ''
                    title = [tag.text.strip() for tag in cells[1].find_all('a') if len(tag.text) > 1]

                    # Identify ISBN pattern
                    isbn_pattern = re.compile(r'\b\d{9,13}(?:;\s*\d{9,13})*\b')
                    isbn = [value for value in title if isbn_pattern.search(value)]

                    # Process title information
                    title_tag = [value for value in title if value not in isbn]
                    title_tag = ' '.join(title_tag)
                    title_tag0 = cells[1].find('b').text.strip() if cells[1].find('b') else ''
                    title_tag = title_tag0 + ' - ' + title_tag if title_tag0 else title_tag
                    title_tag = re.sub(r'\s{2,}', ' ', title_tag.strip())
                    isbn = [value.strip() for value in isbn[0].split(';')] if isbn else []

                    # Extract remaining metadata fields
                    author_tag = cells[2].text.strip()
                    publisher_tag = cells[3].text.strip()
                    year_tag = cells[4].text.strip()
                    language_tag = cells[5].text.strip()
                    pages_tag = cells[6].text.strip()
                    size_tag = cells[7].text.strip()
                    format_tag = cells[8].text.strip()

                    # Find unique ID and download URLs
                    id_tag = cells[1].find('span', class_='badge badge-secondary').text.strip() if cells[1].find('span',
                                                                                                                 class_='badge badge-secondary') else ''
                    id_tag = re.sub(r'\s+', '', id_tag)
                    content_url = [a['href'] for a in cells[9].find_all('a', href=True) if
                                    a['href'][0] == '/' or 'library.lol' in a['href'] or 'sci-hub.ru' in a['href']]
                    content_url[0] = 'https://libgen.li' + content_url[0] if content_url and content_url[0][
                        0] == '/' else content_url[0]

                    # Append extracted data to the metadata list
                    metadata_list.append(
                        {
                            'title': title_tag,
                            'author': author_tag,
                            'publisher': publisher_tag,
                            'year': year_tag,
                            'language': language_tag,
                            'pages': pages_tag,
                            'size': size_tag,
                            'format': format_tag,
                            'thumbnail': thumbnail,
                            'isbn': isbn,
                            'id': id_tag,
                            'content_url': content_url
                        }
                    )
            return metadata_list[:max_entries]
        else:
            self._logger.info("Results Not Found")
            return metadata_list

    def get_json(self):
        """
        Finds and returns a JSON link for additional metadata if available on the page.

        Returns:
            str or None: JSON link or None if no link is found or request fails.
        """
        try:
            nav_tabs = self._soup.find('ul', class_='nav nav-tabs')
            if nav_tabs:
                # Retrieve the last link in the navigation tabs as JSON URL
                json_link = nav_tabs.find_all('a', href=True)[-1]
                href = json_link['href']
                return 'https://libgen.li' + href
        except requests.exceptions.RequestException as e:
            return e.response.text

    @staticmethod
    def resolve_download(url):
        """
        Resolves a download link by scraping the specific download page.

        Args:
            url (str): The URL of the page to retrieve the download link from.

        Returns:
            str or None: Resolved download link, or None if unavailable.
        """
        from ._scrapper_sessions import _Session
        session = _Session(url)
        soup = session.soup
        if soup:
            table = soup.find('table')
            if 'libgen.li' in url:
                return 'https://libgen.li/' + table.find('a')['href'] if table.find('a')['href'] else ''
            elif 'library.lol' in url:
                return table.find('a')['href'] if table.find('a')['href'] else ''
        else:
            return None

    @staticmethod
    def search_fields(title=False, authors=False, series=False, year=False, publisher=False, isbn=False):
        """
        Constructs search field filters based on the specified search parameters.

        Args:
            title (bool): Include title field if True.
            authors (bool): Include authors field if True.
            series (bool): Include series field if True.
            year (bool): Include year field if True.
            publisher (bool): Include publisher field if True.
            isbn (bool): Include ISBN field if True.

        Returns:
            list: List of URL parameter strings for filtering search fields.
        """
        filters = [
            'columns%5B%5D=t' if title else '',
            'columns%5B%5D=a' if authors else '',
            'columns%5B%5D=s' if series else '',
            'columns%5B%5D=y' if year else '',
            'columns%5B%5D=p' if publisher else '',
            'columns%5B%5D=i' if isbn else ''
        ]
        return filters

    @staticmethod
    def search_categories(libgen=False, comics=False, fiction=False, scientific_articles=False, magazines=False,
                          fiction_russian=False, standards=False):
        """
        Constructs search filters based on specified categories.

        Args:
            libgen (bool): Include libgen topic if True.
            comics (bool): Include comics topic if True.
            fiction (bool): Include fiction topic if True.
            scientific_articles (bool): Include scientific articles topic if True.
            magazines (bool): Include magazines topic if True.
            fiction_russian (bool): Include Russian fiction topic if True.
            standards (bool): Include standards topic if True.

        Returns:
            list: List of URL parameter strings for filtering topics.
        """
        filters = [
            'topics%5B%5D=l' if libgen else '',
            'topics%5B%5D=c' if comics else '',
            'topics%5B%5D=f' if fiction else '',
            'topics%5B%5D=a' if scientific_articles else '',
            'topics%5B%5D=m' if magazines else '',
            'topics%5B%5D=r' if fiction_russian else '',
            'topics%5B%5D=s' if standards else ''
        ]
        return filters

    def search(self, query, search_by=None, categories=None, max_results=100, page=1):
        """
        Constructs and initializes a session with a search URL based on the given query and filters.

        Args:
            query (str): Search query string.
            search_by (list): List of field filters from `search_fields`.
            categories (list): List of topic filters from `topics`.
            max_results (int): Maximum number of results to retrieve. Defaults to 100.
            page (int): Page number for pagination. Defaults to 1.
        """
        # Build the search URL based on query, field filters, and topic filters
        url = f'https://libgen.li/index.php?req={query}&'
        if search_by:
            url = url + '&'.join(search_by)
        if categories:
            url = url + '&'.join(categories)
        url = url + f'&res={max_results}&covers=on&showch=on&gmode=on&filesuns=all&page={page}&curtab=f&order=&ordermode=desc'

        # Initialize the session with the constructed URL
        self._initialize_session(url)

    @staticmethod
    def filtered(metadata, title='', authors='', language='', year='', publisher=''):
        """
        Filters metadata based on specified criteria.

        Args:
            metadata (list): List of metadata dictionaries to filter.
            title (str): Filter by title if specified.
            authors (str): Filter by authors if specified.
            language (str): Filter by language if specified.
            year (str): Filter by publication year if specified.
            publisher (str): Filter by publisher if specified.

        Returns:
            list: List of filtered metadata entries.
        """
        filtered_metadata = []

        # Iterate through each metadata entry to apply filters
        for entry in metadata:
            match = True
            if title and title.lower() not in entry.get('title', '').lower():
                match = False
            if authors and authors.lower() not in entry.get('author', '').lower():
                match = False
            if language and language.lower() not in entry.get('language', '').lower():
                match = False
            if year and year.lower() not in entry.get('year', '').lower():
                match = False
            if publisher and publisher.lower() not in entry.get('publisher', '').lower():
                match = False
            if match:
                filtered_metadata.append(entry)

        return filtered_metadata
