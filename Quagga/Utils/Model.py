import numpy as np


class Model:
	def __init__(self):
		self.line_length = 80
		self.num_possible_chars = len(self.char_index())

		self.zones = None
		self.with_crf = ""
		self.trainset = ""

		self.line_model = None
		self.line_functions = []

		self.model = None
		self.encoder = None

	def predict(self, text_lines):
		if self.with_crf:
			text_embedded = self._embed(text_lines, self.line_functions)
			y = self.model.predict(np.array([text_embedded])).tolist()[0]
		else:
			text_embedded = self._embed(text_lines)
			y = self.line_model.predict(text_embedded).tolist()
		return y, text_lines, self.encoder

	@staticmethod
	def char_index():
		return list(' '
		            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
		            'abcdefghijklmnopqrstuvwxyz'
		            '0123456789'
		            '@€-_.:,;#\'+*~\?}=])[({/&%$§"!^°|><´`\n')

	def _embed(self, lines, embedding_functions=None):
		x = np.zeros((len(lines), self.line_length, self.num_possible_chars + 1))

		for i, line in enumerate(lines):
			for j, char in enumerate(line):
				if j >= self.line_length:
					break
				x[i][j][self.char_index().index(char) + 1 if char in self.char_index() else 0] = 1

		if embedding_functions is None:
			return x
		x = np.concatenate([embedding_function(x)
		                    for embedding_function in embedding_functions], axis=1)
		return x
