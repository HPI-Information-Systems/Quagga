#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import tensorflow as tf

from Utils.ModelBuilder import ModelBuilder
from Utils.BlockParser import BlockParser
from Utils.EmailReader import DirectoryReader, ListReaderRawEmailTexts, ListReaderExtractedBodies
from Utils.Email import Email, serialize_quagga_email

from pprint import pprint
import json
import os
import shutil

from enum import IntEnum

class State(IntEnum):
	INIT = 0
	BODY = 1
	PREDICT = 2
	PARSE = 3

class EmailIterator:
	def __init__(self, quagga, emails, working_directory, emails_input, email_func, stage, state):
		self.quagga = quagga
		self.emails = emails
		self.working_directory = working_directory
		self.emails_input = emails_input
		self.email_func = email_func
		self.stage = stage
		self.state = state

	def __next__(self):
		try:
			filename = next(self.emails).filename
			email_input = next(self.emails_input)
		except StopIteration:
			self.quagga.state = self.state
			raise StopIteration
		email_output = self.email_func(email_input)
		self.quagga._store_email(self.working_directory, filename, self.stage, email_output)


class EmailProcessor:
	def __init__(self, quagga, emails, working_directory, emails_input, email_func, stage, state):
		self.quagga = quagga
		self.emails = emails
		self.working_directory = working_directory
		self.emails_input = emails_input
		self.email_func = email_func
		self.stage = stage
		self.state = state

	def __iter__(self):
		return EmailIterator(self.emails, self.working_directory, self.emails_input, self.email_func, self.stage, self.state)


class Quagga:

	def __init__(self, email_reader, tmp_dir='.quagga/', model_builder=ModelBuilder(), model=None,
	             block_parser=BlockParser()):

		self.state = State.INIT

		# READ
		self.emails_input = email_reader
		self.working_directory = tmp_dir
		if os.path.exists(self.working_directory):
			shutil.rmtree(self.working_directory)
		os.makedirs(self.working_directory)

		# MODEL

		self.model_builder = model_builder
		self.model = model

		print("building model...")
		self.model_builder = model_builder
		if model is None:
			self.model_builder = model_builder
			self.model_builder.build()
			self.model = model_builder.quagga_model
			self.model.graph = tf.get_default_graph()
		else:
			self.model = model

		self.graph = tf.get_default_graph()
		# PREDICT

		# PARSE
		self.block_parser = block_parser

	"""def required_state(required_state):  # first parameter is not self
		def decorator(func):
			@wraps(func)
			def wrapper(inst, *args, **kwargs):
				if inst.state < required_state:
					inst.pipeline[required_state]()
				inst.state = required_state
				return func(inst, *args, **kwargs)

			return wrapper

		return decorator"""

	@property
	def emails_body(self):
		#return EmailProcessor(self, self.emails_input, self.working_directory, self.emails_input, lambda email: email.clean_body, 'body', State.BODY)
		for email_input in self.emails_input:
			email_body = email_input.clean_body
			self._store_email(self.working_directory, email_input.filename, 'body', email_body)
			yield email_body

	@property
	def emails_predicted(self):
		for email_body, email_input in zip(self.emails_body, self.emails_input):
			email_prediction = self._get_predictions(email_body)
			self._store_email(self.working_directory, email_input.filename, 'predicted', email_prediction)
			yield email_prediction

	def emails_parsed(self, prediction_reader=None):
		if prediction_reader is None:
			prediction_reader = self.emails_predicted
		for email_prediction, email_input in zip(prediction_reader, self.emails_input):
			email_parsed = self.block_parser.parse_predictions(email_prediction, email_input)
			self._store_email(self.working_directory, email_input.filename, 'parsed', email_parsed)
			yield email_parsed

	@staticmethod
	def _email_storage(input=None, predicted=None, parsed=None):
		return {'input': input,
		        'predicted': predicted,
		        'parsed': parsed}

	def store(self, foldername):

		def email_storages():
			for email_input, email_predicted, email_parsed in zip(self.emails_input, self.emails_predicted,
			                                                      self.emails_parsed()):
				yield self._email_storage(email_input, email_predicted, email_parsed)

		self._store(foldername, 'quagga', email_storages())

	def _store(self, foldername, stage, emails):
		if not os.path.exists(foldername):
			os.makedirs(foldername)

		for input, email in zip(self.emails_input, emails):
			self._store_email(foldername, input.filename, stage, email)
		print("stored " + stage + " in " + foldername)

	def _store_email(self, foldername, filename, stage, email):
		path = os.path.abspath(foldername)
		filename = path + '/' + filename + '.' + stage + '.json'
		with open(filename, 'w+') as fp:
			json.dump({stage: email}, fp, default=serialize_quagga_email)

	def store_input(self, foldername):
		self._store(foldername, 'input', self.emails_input)

	def store_predicted(self, foldername):
		self._store(foldername, 'predicted', self.emails_predicted)

	def store_parsed(self, foldername):
		self._store(foldername, 'parsed', self.emails_parsed())

	def print_predictions(self):
		for email_predicted in self.emails_predicted:
			for line_prediction in email_predicted:
				print(str(line_prediction['predictions']) + ' ' + line_prediction['text'])

	def _build_model(self, model_builder=ModelBuilder(), model=None):
		with self.graph.as_default():
			print("building model...")
			self.model_builder = model_builder
			if model is None:
				self.model_builder = model_builder
				self.model_builder.build()
				self.model = model_builder.quagga_model
			else:
				self.model = model

	def _get_predictions(self, mail_text):
		with self.graph.as_default():
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

	quagga = Quagga(DirectoryReader(test_dir))

	print("========================= input ")
	for input in quagga.emails_input:
		pprint(input)
	print("========================= bodies ")
	for body in quagga.emails_body:
		pprint(body)
	print("========================= predictions ")
	for prediction in quagga.emails_predicted:
		pprint(prediction)
	print("========================= parsed ")
	for parsed in quagga.emails_parsed():
		pprint(parsed)

	quagga.store(test_dir)
