class RAGConfig:
	"""
	Configuration class for individual RAG instances.
	"""

	def __init__(
		self,
		chat_model: str = 'gpt-4o-mini',
		embedding_model: str = 'text-embedding-3-large',
		system_prompt: str = 'You are a helpful assistant that answers questions based on the provided context. Be concise and accurate.'
	):
		self.chat_model = chat_model
		self.embedding_model = embedding_model
		self.system_prompt = system_prompt

	@classmethod
	def from_dict(cls, data: dict) -> 'RAGConfig':
		"""Create RAGConfig from dictionary."""
		return cls(
			chat_model=data.get('chat_model', 'gpt-4o-mini'),
			embedding_model=data.get('embedding_model', 'text-embedding-3-large'),
			system_prompt=data.get('system_prompt', 'You are a helpful assistant that answers questions based on the provided context. Be concise and accurate.')
		)

	def to_dict(self) -> dict:
		"""Convert RAGConfig to dictionary."""
		return {
			'chat_model': self.chat_model,
			'embedding_model': self.embedding_model,
			'system_prompt': self.system_prompt
		}
