import openai
from pathlib import Path
from typing import Literal, cast
from collections.abc import Callable

from llama_index.core import VectorStoreIndex
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI

from src.config import OPENAI_API_KEY
from src.rag_config import RAGConfig
from src.types import DocumentItem, SearchResultItem, SearchResultUrl
from openai.types.responses import ResponseOutputItem


def search(query: str, search_number: Literal["low", "medium", "high"] = "medium") -> SearchResultItem:
	"""
	Search the web for information. Use a detailed plain text question as input.
	"""

	response = openai.responses.create(
		model="gpt-5-mini",
		input=query,
		reasoning={
			"effort": "low",
		},
		text={
			"verbosity": "high"
		},
		tools=[{
			"type": "web_search_preview",
			"search_context_size": search_number,
		}],
	)

	urls: list[SearchResultUrl] = []

	def extract_urls_from_output(output_item: ResponseOutputItem):
		if output_item.type != 'message':
			return
		for content_item in output_item.content:
			if content_item.type != 'output_text':
				continue
			for annotation in content_item.annotations:
				if annotation.type == 'url_citation':
					urls.append(SearchResultUrl(
						title=annotation.title,
						url=annotation.url
					))

	if response.output:
		for output_item in response.output:
			try:
				extract_urls_from_output(output_item)
			except Exception:
				continue

	result: SearchResultItem = {
		'content': response.output_text or 'No answer found.',
		'urls': urls
	}
	return result


def read_file_tool(rel_path: str) -> str:
	"""
	Read the content of a specific file in data/files. Input: relative file path from data/files.
	"""
	base = Path("data/files")
	file_path = base / rel_path
	if not file_path.exists() or not file_path.is_file():
		return f"File not found: {rel_path}"
	try:
		return file_path.read_text(encoding="utf-8")
	except Exception as e:
		return f"Error reading file: {e}"


def list_files_tool(rel_dir: str, max_depth: int = 1) -> list[str]:
	"""
	List files, folders and symlinks in a directory in data/files. Input: relative directory path from data/files.
	"""
	base = Path("data/files")
	dir_path = base / rel_dir
	if not dir_path.exists() or not dir_path.is_dir():
		return [f"Directory not found: {rel_dir}"]

	files: list[str] = []
	for f in dir_path.iterdir():
		if max_depth > 0:
			if f.is_dir():
				files.extend(list_files_tool(str(f.relative_to(base)), max_depth - 1))
			continue

		size = f.stat().st_size
		formatted_size = f"{size / 1024:.2f} KB" if size < 1024 else f"{size / 1024 / 1024:.2f} MB"

		path = f.relative_to(base)
		if f.is_file():
			files.append(f"{path} (file, {formatted_size})")
		elif f.is_dir():
			files.append(f"{path} (folder, {formatted_size})")
		elif f.is_symlink():
			files.append(f"{path} (symlink, {formatted_size})")

	return sorted(files)


def get_agent(
	rag_name: str,
	config: RAGConfig,
	project_summary: str,
	load_index: Callable[[str], VectorStoreIndex],
):
	"""
	Return a FunctionAgent for the given rag_name, with tools for local RAG, DuckDuckGo search, file read, and file list.
	"""

	complete_system_prompt = f"""
You are a helpful assistant that answers questions based on the provided context. Be accurate and do not hallucinate or make up information.
If the user asks about anything related to {rag_name} or that could be related to that, use the `rag` tool.
If the user asks for a file, use the read_file tool, you can search for the file using the `list_files` tool.
If the user asks for a list of files/folders/symlinks, use the `list_files` tool.
If you need to search the web or are unsure about the question, use the `search` tool.

Project name: {rag_name}
--------------------------------

Project summary:
{project_summary}
--------------------------------

User instructions:
{config.system_prompt}
""".strip()

	llm = OpenAI(
		api_key=OPENAI_API_KEY,
		model=config.chat_model,
		system_prompt=complete_system_prompt
	)


	def rag_tool(rag_name: str, query: str, search_number: Literal["very_low", "low", "medium", "high"] = "medium") -> list[DocumentItem]:
		"""
		Search relevant documents from the '{rag_name}' document index. Use a detailed search query as input.
		Search number:
		- very_low: 4 documents
		- low: 10 documents
		- medium: 30 documents
		- high: 60 documents
		"""
		search_number_map = {
			"very_low": 4,
			"low": 10,
			"medium": 30,
			"high": 60
		}

		index = load_index(rag_name)
		retriever = index.as_retriever(similarity_top_k=search_number_map[search_number])

		response = retriever.retrieve(query)
		return [
			DocumentItem(
				content=node.text,
				source=cast(str, node.node.metadata.get("file_path", ""))
			)
			for node in response
		]


	agent = FunctionAgent(
		tools=[rag_tool, search, read_file_tool, list_files_tool],
		llm=llm,
		system_prompt=complete_system_prompt,
		# verbose=True,
	)
	return agent
