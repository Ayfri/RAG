"""
Utility functions for the RAG application.

General-purpose utilities that can be reused across different modules.
"""

import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import html2text
from llama_index.core.schema import Document

from src.logger import get_logger

logger = get_logger(__name__)


def filter_documents_by_include_globs(documents: list[Document], include_globs: list[str]) -> list[Document]:
	"""Filter documents list based on include glob patterns applied to their file paths."""
	import fnmatch

	filtered_docs: list[Document] = []

	for doc in documents:
		file_path = str(doc.metadata.get('file_path', ''))
		if file_path:
			file_name = Path(file_path).name

			included = False
			for include_pattern in include_globs:
				if fnmatch.fnmatch(file_name, include_pattern) or fnmatch.fnmatch(file_path, include_pattern):
					included = True
					break

			if included:
				filtered_docs.append(doc)

	return filtered_docs


def filter_files_by_globs(files: list[str], include_globs: list[str], exclude_globs: list[str]) -> list[str]:
	"""Filter files list based on include and exclude glob patterns."""
	import fnmatch

	filtered_files: list[str] = []

	for file in files:
		excluded = False
		for exclude_pattern in exclude_globs:
			if fnmatch.fnmatch(file, exclude_pattern):
				excluded = True
				break

		if excluded:
			continue

		included = False
		for include_pattern in include_globs:
			if fnmatch.fnmatch(file, include_pattern):
				included = True
				break

		if included:
			filtered_files.append(file)

	return filtered_files


def get_dir_stats(path: Path) -> tuple[int, int]:
	"""Return (file_count, total_size) for all files under path recursively."""
	file_count = 0
	total_size = 0
	for f in path.rglob('*'):
		if f.is_file():
			file_count += 1
			try:
				total_size += f.stat().st_size
			except OSError:
				pass
	return file_count, total_size


def is_json_object(text: str) -> bool:
	"""Simple check for complete JSON objects only."""
	if not text or not text.strip():
		return False

	text = text.strip()

	if (text.startswith('{') and text.endswith('}')) or (text.startswith('[') and text.endswith(']')):
		try:
			json.loads(text)
			return True
		except:
			return False

	return False


def fetch_url_content(url: str) -> Document:
	"""
	Fetch content from a URL and convert it to a Document.
	Handles HTML parsing, markdown conversion, and metadata extraction.
	"""
	try:
		parsed_url = urlparse(url)
		if not parsed_url.scheme or not parsed_url.netloc:
			raise Exception(f"Invalid URL format: {url}")
	except Exception:
		raise Exception(f"Invalid URL: {url}")

	try:
		with requests.Session() as session:
			session.headers.update({
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
				'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
				'Accept-Language': 'en-US,en;q=0.5',
				'Accept-Encoding': 'gzip, deflate',
				'Connection': 'keep-alive',
				'Upgrade-Insecure-Requests': '1',
			})

			timeout = (10, 30)
			max_retries = 3
			retry_delay = 1

			response: requests.Response | None = None
			for attempt in range(max_retries):
				try:
					response = session.get(
						url,
						timeout=timeout,
						allow_redirects=True,
						verify=True
					)
					response.raise_for_status()
					break

				except requests.exceptions.Timeout as e:
					if attempt == max_retries - 1:
						raise Exception(f"Request timeout after {max_retries} attempts: {url}")
					time.sleep(retry_delay * (attempt + 1))
					continue

				except requests.exceptions.ConnectionError as e:
					if attempt == max_retries - 1:
						raise Exception(f"Connection failed after {max_retries} attempts: {url}")
					time.sleep(retry_delay * (attempt + 1))
					continue

				except requests.exceptions.RequestException as e:
					raise e

			if response is None:
				raise Exception(f"No response received from {url}")

			content_type = response.headers.get('content-type', '').lower()
			if not any(ct in content_type for ct in ['text/html', 'text/plain', 'application/xhtml+xml']):
				raise Exception(f"Unsupported content type: {content_type}")

			content_length = response.headers.get('content-length')
			if content_length and int(content_length) > 10 * 1024 * 1024:
				raise Exception(f"Content too large: {content_length} bytes")

			soup = BeautifulSoup(response.content, 'html.parser')

		for script in soup(["script", "style"]):
			script.decompose()

		title = soup.find('title')
		title_text = title.get_text().strip() if title else ''

		h = html2text.HTML2Text()
		h.body_width = 0

		html_content = str(soup)
		markdown_content = h.handle(html_content)

		markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
		markdown_content = re.sub(r' {3,}', ' ', markdown_content)
		markdown_content = markdown_content.strip()

		metadata = {
			'file_path': url,
			'url': url,
			'domain': parsed_url.netloc,
			'title': title_text,
			'source_type': 'web_page',
			'content_type': 'text/markdown',
			'content_length': len(markdown_content),
			'response_status': response.status_code,
			'response_headers': dict(response.headers)
		}

		document = Document(
			text=markdown_content,
			metadata=metadata
		)

		return document

	except requests.exceptions.HTTPError as e:
		if e.response.status_code == 404:
			raise Exception(f"URL not found (404): {url}")
		elif e.response.status_code == 403:
			raise Exception(f"Access forbidden (403): {url}")
		elif e.response.status_code == 401:
			raise Exception(f"Unauthorized access (401): {url}")
		elif e.response.status_code >= 500:
			raise Exception(f"Server error ({e.response.status_code}): {url}")
		else:
			raise Exception(f"HTTP error {e.response.status_code}: {url}")
	except requests.exceptions.ConnectionError:
		raise Exception(f"Connection failed: {url}")
	except requests.exceptions.Timeout:
		raise Exception(f"Request timeout: {url}")
	except requests.exceptions.RequestException as e:
		raise Exception(f"Failed to fetch URL {url}: {str(e)}")
	except Exception as e:
		raise Exception(f"Failed to process URL {url}: {str(e)}")
