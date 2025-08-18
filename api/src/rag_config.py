from pydantic import BaseModel, Field


class RAGConfig(BaseModel):
	"""
	Configuration class for individual RAG instances.
	"""
	chat_model: str = 'gpt-5-mini'
	embedding_model: str = 'text-embedding-3-large'
	system_prompt: str = 'You are a helpful assistant that answers questions based on the provided context. Be concise and accurate.'
	file_filters: dict[str, dict[str, list[str]]] = Field(default_factory=dict)
	"""
	file_filters structure: {"folder_or_symlink_name": {"include": ["**/*"], "exclude": []}}
	Default includes everything with '**/*'
	"""


	def get_file_filters_for_path(self, path_name: str) -> dict[str, list[str]]:
		"""
		Get file filters for a specific path (folder or symlink).

		:param path_name: Name of the folder or symlink
		:return: Dictionary with 'include' and 'exclude' glob patterns
		"""
		if path_name in self.file_filters:
			filters = self.file_filters[path_name]
			return {
				'include': filters.get('include', ['**/*']),
				'exclude': filters.get('exclude', [])
			}
		else:
			# Default: include everything
			return {
				'include': ['**/*'],
				'exclude': []
			}
