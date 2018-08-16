# -*- coding: utf-8 -*-

import tensorflow as tf

from quaggaModelBuilder import QuaggaModelBuilder
from quaggaBlockParser import QuaggaBlockParser
from quaggaReader import QuaggaDirectoryReader, QuaggaListReaderRawEmailTexts, QuaggaListReaderExtractedBodies
from quaggaEmail import QuaggaEmail

from pprint import pprint
from enum import IntEnum
from functools import wraps
import json
import sys, os
from pathlib import Path

class State(IntEnum):
	INIT = 0
	READ = 1
	MODEL = 2
	PREDICT = 3
	PARSE = 4


def serialize(obj):
	"""JSON serializer for objects not serializable by default json code"""

	if isinstance(obj, QuaggaEmail):
		# todo could solve this with (awful) metaprogramming
		serial = {
			'sent' : obj.sent,
			'file': obj.file,
			'folder': obj.folder,
			'id': obj.id,
			'mailbox': obj.mailbox,
			'subject': obj.subject,
			'sender': obj.sender,
			'xsender': obj.xsender,
			'to': obj.to,
			'xto': obj.xto,
			'cc': obj.cc,
			'xcc': obj.xcc,
			'bcc': obj.bcc,
			'xbcc': obj.xbcc,
			'body': obj.body,
			'clean_body': obj.clean_body,
		}
		return serial
	else:
		raise TypeError(" Object of type " + type(obj) + " is not JSON serializable")


class Quagga:
	# todo block parser (refactoring)
	# todo block parser file format??
	def __init__(self):
		self.state = State.INIT
		self.pipeline = [lambda: print(self.status),
		                 lambda: sys.exit("error: you must specify emails to work on before proceeding"),
		                 lambda: self.build_model(),
		                 lambda: self.predict(),
		                 lambda: self.parse()]

		self.emails = []

		# READ
		self.email_reader = None

		# MODEL
		self.model_builder = None
		self.model = None

		# PREDICT

		# PARSE
		self.block_parser = None

	def required_state(required_state, next_state): #first parameter is not self
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

	@staticmethod
	def _email_storage(quagga_email=None, predicted=None, parsed=None):
		return {'quagga_email': quagga_email,
		        'predicted': predicted,
		        'parsed': parsed}

	@property
	@required_state(State.READ, State.READ)
	def emails_quagga_email(self):
		return [email_storage['quagga_email'] for email_storage in self.emails]

	@property
	@required_state(State.READ, State.READ)
	def emails_body(self):
		return [email_storage['quagga_email'].clean_body for email_storage in self.emails]

	@property
	@required_state(State.PREDICT, State.PREDICT)
	def emails_predicted(self):
		return [email_storage['predicted'] for email_storage in self.emails]

	@property
	@required_state(State.PARSE, State.PARSE)
	def emails_parsed(self):
		return [email_storage['parsed'] for email_storage in self.emails]

	@required_state(State.INIT, State.READ)
	def read(self, email_reader):
		print("reading emails...")
		self.email_reader = email_reader
		self.emails = [self._email_storage(quagga_email = quagga_email) for quagga_email in self.email_reader]


	@required_state(State.READ, State.MODEL)
	def build_model(self, model_builder=QuaggaModelBuilder(), model=None):
		print("building model...")
		self.model_builder = model_builder
		if model is None:
			self.model_builder.quagga_model.graph = tf.get_default_graph()
			self.model_builder = model_builder
			self.model_builder.build()
			self.model = model_builder.quagga_model
		else:
			self.model = model

	@required_state(State.MODEL, State.PREDICT)
	def predict(self):
		print("predicting...")
		for email_storage, body in zip(self.emails, self.emails_body):
			email_storage['predicted'] = self._get_predictions(body)

	@required_state(State.PREDICT, State.PARSE)
	def parse(self, block_parser=QuaggaBlockParser()):
		print("parsing...")
		self.block_parser = block_parser

		for email_storage, prediction, quagga_email in zip(self.emails, self.emails_predicted, self.emails_quagga_email):
			email_storage['parsed'] = self.block_parser.parse_predictions(prediction, quagga_email)



	def store(self, foldername):
		self.store_quagga_email(foldername)
		self.store_predicted(foldername)
		self.store_parsed(foldername)



	def _store(self, foldername, feature):
		path = os.path.abspath(foldername)

		for email_storage in self.emails:
			filename = email_storage['quagga_email'].filename
			with open(path + '/' + filename + '.' + feature + '.json', 'a+') as fp:
				json.dump(email_storage[feature], fp, default=serialize)

		print("stored " + feature + " in " + foldername)

	def store_quagga_email(self, foldername):
		# todo serialize quagga_email
		self._store(foldername, 'quagga_email')

	def store_predicted(self, foldername):
		self._store(foldername, 'predicted')

	def store_parsed(self, foldername):
		self._store(foldername, 'parsed')

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
		#quagga.read(QuaggaListReaderRawEmailTexts([f.read()]))
		quagga.read(QuaggaDirectoryReader('testMails'))

		# quagga.build_model()
		# quagga.predict()
		# quagga.parse()

		pprint(quagga.emails_body)
		pprint(quagga.emails_predicted)
		pprint(quagga.emails_parsed)

		pprint(quagga.emails)

		quagga.store("testMailsQuaggaed")
