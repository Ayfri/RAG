import openai
from pathlib import Path
from typing import Callable
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
from llama_index.core.tools import FunctionTool, RetrieverTool
from src.config import OPENAI_API_KEY
from llama_index.core.schema import NodeWithScore
from llama_index.core import VectorStoreIndex
from src.rag_config import RAGConfig


class SearchResultUrl(dict):
	title: str
	url: str


class SearchResult(dict):
	content: str
	urls: list[SearchResultUrl]


def search(query: str) -> SearchResult:
	"""
	Search the web for information. Use a detailed plain text question as input.
	"""
	response = openai.chat.completions.create(
		model="gpt-4o-search-preview",
		messages=[{"role": "user", "content": query}],
	)
	result = SearchResult(
		content=response.choices[0].message.content or "No answer found.",
		urls=[
			SearchResultUrl(
				title=annotation.url_citation.title,
				url=annotation.url_citation.url
			)
			for annotation in response.choices[0].message.annotations or []
		]
	)
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
	load_index: Callable[[str], VectorStoreIndex],
):
	"""
	Return a FunctionAgent for the given rag_name, with tools for local RAG, DuckDuckGo search, file read, and file list.
	- config: RAGConfig instance
	- load_index: function to load the index for rag_name
	"""
	complete_system_prompt = f"""
You are a helpful assistant that answers questions based on the provided context. Be concise and accurate.

You have access to the following tools:
- rag: Answer questions using the '{rag_name}' document index. Use a detailed plain text question as input.
- DuckDuckGoSearch: Search the web for information. Use a detailed plain text question as input.
- read_file: Read the content of a specific file in data/files. Input: relative file path from data/files.
- list_files: List files in a directory in data/files. Input: relative directory path from data/files.

If you are not sure about the answer, it has a big chance to be related to the documents you have access to, so you should use the {rag_name}_rag tool.

User instructions:
{config.system_prompt}
""".strip()

	llm = OpenAI(
		api_key=OPENAI_API_KEY,
		model=config.chat_model,
		system_prompt=complete_system_prompt
	)


	def rag_tool(rag_name: str, query: str) -> list[NodeWithScore]:
		"""
		Answer questions using the '{rag_name}' document index. Use a detailed plain text question as input.
		"""
		index = load_index(rag_name)
		retriever = index.as_retriever(similarity_top_k=20)

		response = retriever.retrieve(query)
		return response


	agent = FunctionAgent(
		tools=[rag_tool, search, read_file_tool, list_files_tool],
		llm=llm,
		system_prompt=complete_system_prompt,
		verbose=True,
	)
	return agent
