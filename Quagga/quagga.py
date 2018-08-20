#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

import tensorflow as tf

from quaggaModelBuilder import QuaggaModelBuilder
from quaggaBlockParser import QuaggaBlockParser
from quaggaReader import QuaggaDirectoryReader, QuaggaListReaderRawEmailTexts, QuaggaListReaderExtractedBodies
from quaggaEmail import QuaggaEmail, serialize_quagga_email

from pprint import pprint
from enum import IntEnum
from functools import wraps
import json
import sys, os
import copy


# todo
# am anfang spezifiert man nur die ganzen sachen
# erst am ende wird alles berechnet wenn man auf die sachen zugreift
# das wird pro mail einzeln gemacht und sie wird nicht zwischengespeichert

class Quagga:

	def __init__(self, email_reader, model_builder=QuaggaModelBuilder(), model=None, block_parser=QuaggaBlockParser()):

		# READ
		self.emails_input_reader = email_reader

		# MODEL

		print("building model...")
		self.model_builder = model_builder
		if model is None:
			self.model_builder.quagga_model.graph = tf.get_default_graph()
			self.model_builder = model_builder
			self.model_builder.build()
			self.model = model_builder.quagga_model
		else:
			self.model = model

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
	def emails_input(self):
		return copy.copy(self.emails_input_reader)

	@property
	def emails_body(self):
		for email in self.emails_input:
			yield email.clean_body

	@property
	def emails_predicted(self):
		for body in self.emails_body:
			yield self._get_predictions(body)

	@property
	def emails_parsed(self):
		for email_prediction, email_input in zip(self.emails_predicted, self.emails_input):
			yield self.block_parser.parse_predictions(email_prediction, email_input)

	@staticmethod
	def _email_storage(input=None, predicted=None, parsed=None):
		return {'input': input,
		        'predicted': predicted,
		        'parsed': parsed}

	def store(self, foldername):

		def email_storages():
			for email_input, email_predicted, email_parsed in zip(self.emails_input, self.emails_predicted,
			                                                      self.emails_parsed):
				yield self._email_storage(email_input, email_predicted, email_parsed)

		self._store(foldername, 'quaggaed', email_storages())

	def _store(self, foldername, stage, emails):
		path = os.path.abspath(foldername)

		for input, email in zip(self.emails_input, emails):
			filename = input.filename
			with open(path + '/' + filename + '.' + stage + '.json', 'w+') as fp:
				json.dump({stage: email}, fp, default=serialize_quagga_email)

		print("stored " + stage + " in " + foldername)

	def store_input(self, foldername):
		self._store(foldername, 'input', self.emails_input)

	def store_predicted(self, foldername):
		self._store(foldername, 'predicted', self.emails_predicted)

	def store_parsed(self, foldername):
		self._store(foldername, 'parsed', self.emails_parsed)

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

	quagga = Quagga(QuaggaDirectoryReader(test_dir))

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
	for parsed in quagga.emails_parsed:
		pprint(parsed)


	quagga.store(test_dir)
