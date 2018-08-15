# -*- coding: utf-8 -*-

import tensorflow as tf

from quaggaModelBuilder import QuaggaModelBuilder
from quaggaBlockParser import QuaggaBlockParser
from quaggaReader import QuaggaDirectoryReader, QuaggaListReaderRawEmailTexts, QuaggaListReaderExtractedBodies

from pprint import pprint
from enum import IntEnum
from functools import wraps


class State(IntEnum):
	INIT = 0
	READ = 1
	MODEL = 2
	PREDICT = 3
	PARSE = 4


class Quagga:
	# todo block parser (refactoring)
	# todo block parser file format??
	def __init__(self):
		self.state = State.INIT
		self.pipeline = [lambda: print(self.status),
		                 lambda: print(self.status),
		                 lambda: self.build_model(),
		                 lambda: self.predict(),
		                 lambda: self.parse()]

		# READ
		self.email_reader = None
		self.email_bodies = []

		# MODEL
		self.model_builder = None
		self.model = None

		# PREDICT
		self.emails_predicted = []

		# PARSE
		self.block_parser = None
		self.emails_parsed = []

	def transition(required_state, next_state):
		def decorator(func):
			@wraps(func)
			def wrapper(inst, *args, **kwargs):
				if inst.state < required_state:
					inst.pipeline[required_state]()
				inst.state = next_state
				return func(inst, *args, **kwargs)

			return wrapper

		return decorator

	@property
	def status(self):
		if self.state is State.INIT:
			return "Quagga initialized. Read emails using read(email_reader)."
		elif self.state is State.READ:
			return "Emails read. Load model using build_model(model_builder) and predict using predict()."
		elif self.state is State.MODEL:
			return "Model loaded. Read emails using read(email_reader) and predict using predict()."
		elif self.state is State.PREDICT:
			return "Zones predicted. Parse emails using them with parse(block_parser)."
		elif self.state is State.PARSE:
			return "Emails parsed. Store using store(filename)."

	@transition(State.INIT, State.READ)
	def read(self, email_reader):
		self.email_reader = email_reader
		self.email_bodies = [email.clean_body for email in self.email_reader]

	@transition(State.READ, State.MODEL)
	def build_model(self, model_builder=QuaggaModelBuilder(), model=None):

		self.model_builder = model_builder
		if model is None:
			self.model_builder.quagga_model.graph = tf.get_default_graph()
			self.model_builder = model_builder
			self.model_builder.build()
			self.model = model_builder.quagga_model
		else:
			self.model = model


	@transition(State.MODEL, State.PREDICT)
	def predict(self):
		self.emails_predicted = [self._get_predictions(email_body) for email_body in self.email_bodies]

	@transition(State.PREDICT, State.PARSE)
	def parse(self, block_parser=QuaggaBlockParser()):

		self.block_parser = block_parser

		for email_predicted, email_raw_parser in zip(self.emails_predicted, self.email_reader):
			blocks = self.block_parser.parse_predictions(email_predicted, email_raw_parser)

			self.emails_parsed.append(blocks)




	def store(self, filename):
		# todo store predictions
		# einmal dict zurückgeben
		# einfach das was rauskommt speichern
		# bisschen zusammenstellen was man haben mchte
		# json speichern
		pass

	def store_emails_parsed(self):
		"""available data:
		email_reader
		email_bodies
		emails_predicted
		emails_parsed
		"""
		# todo store parsed emails
		pass

	def print_predictions(self):
		for email_predicted in self.emails_predicted:
			for line_prediction in email_predicted:
				print(str(line_prediction['predictions']) + ' ' + line_prediction['text'])

	def _get_predictions(self, mail_text):
		text_raw = mail_text
		text_lines = text_raw.split('\n')

		return self._prettify_prediction(*self.model.predict(text_lines))

	def _prettify_prediction(self, y, text_lines, label_encoder):
		labels = label_encoder.classes_
		predictions = []
		for yi, line in zip(y, text_lines):
			line_prediction = {
				'text': line,
				'predictions': {}
			}
			for li, label in enumerate(labels):
				line_prediction['predictions'][label] = yi[li]
			predictions.append(line_prediction)
		return predictions


if __name__ == '__main__':
	test_dir = "testMails"

	with open(test_dir + "/bass-e__sent_mail_20.txt", "r", errors='ignore') as f:
		quagga = Quagga()
		quagga.read(QuaggaListReaderRawEmailTexts([f.read()]))
		#quagga.build_model()
		#quagga.predict()
		quagga.parse()

		pprint(quagga.email_bodies)
		pprint(quagga.emails_predicted)
		pprint(quagga.emails_parsed)
