class RAGConfig:
	"""
	Configuration class for individual RAG instances.
	"""

	def __init__(
		self,
		chat_model: str = 'gpt-4o-mini',
		embedding_model: str = 'text-embedding-3-large',
		system_prompt: str = 'You are a helpful assistant that answers questions based on the provided context. Be concise and accurate.',
		file_filters: dict[str, dict[str, list[str]]] | None = None
	):
		self.chat_model = chat_model
		self.embedding_model = embedding_model
		self.system_prompt = system_prompt
		# file_filters structure: {"folder_or_symlink_name": {"include": ["**/*"], "exclude": []}}
		# Default includes everything with '**/*'
		self.file_filters = file_filters or {}

	@classmethod
	def from_dict(cls, data: dict) -> 'RAGConfig':
		"""Create RAGConfig from dictionary."""
		return cls(
			chat_model=data.get('chat_model', 'gpt-4o-mini'),
			embedding_model=data.get('embedding_model', 'text-embedding-3-large'),
			system_prompt=data.get('system_prompt', 'You are a helpful assistant that answers questions based on the provided context. Be concise and accurate.'),
			file_filters=data.get('file_filters', {})
		)

	def to_dict(self) -> dict:
		"""Convert RAGConfig to dictionary."""
		return {
			'chat_model': self.chat_model,
			'embedding_model': self.embedding_model,
			'system_prompt': self.system_prompt,
			'file_filters': self.file_filters
		}

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
