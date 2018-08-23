#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-


from Utils.ModelBuilder import ModelBuilder
from Utils.BlockParser import BlockParser
from Utils.EmailReader import DirectoryReader, EmailDirectoryReader, TempQuaggaReader, ListReaderRawEmailTexts, \
	ListReaderExtractedBodies
from Utils.Email import Email, serialize_quagga_email
from Utils.EmailProcessor import EmailProcessor

import tensorflow as tf
from pprint import pprint
import json
from enum import IntEnum

import os
import sys
import shutil


class State(IntEnum):
	INIT = 0
	PREDICT = 1
	PARSE = 2


class Quagga:

	def __init__(self, email_reader, output_dir, model_builder=ModelBuilder(), model=None,
	             block_parser=BlockParser()):

		self.state = State.INIT
		self.output_dir = output_dir

		# READ
		self.emails_input = email_reader

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

	@property
	def emails_body(self):
		for email in self.emails_input:
			self._store_email(self.output_dir, email.filename, 'quagga.input', email)
			yield email.clean_body

	def emails_predicted(self, input_reader=None):  # todo use decorator for tempReaders
		if self.state >= State.PREDICT:
			return TempQuaggaReader('predicted', self.output_dir)
		if input_reader is None:
			input_reader = self.emails_body
		else:
			print("reading bodies from .quagga files...")

		return EmailProcessor(self, self.emails_input, self.output_dir, input_reader,
		                      lambda email_body, _: self._predict(email_body), 'predicted', State.PREDICT)

	def emails_parsed(self, prediction_reader=None):
		if self.state >= State.PARSE:
			return TempQuaggaReader('parsed', self.output_dir)
		if prediction_reader is None:
			prediction_reader = self.emails_predicted()
		else:
			print("reading predictions from .quagga files...")
		return EmailProcessor(self, self.emails_input, self.output_dir, prediction_reader,
		                      lambda email_prediction, email_input: self._parse(
			                      email_prediction, email_input), 'parsed', State.PARSE)




	# this is optimized so things are loaded only once into memory and not written and read from disk immediately after
	def store_all(self, foldername):
		for input in self.emails_input:
			self._store_email(foldername, input.filename, 'quagga.input', input)
			predicted = self._predict(input.clean_body)
			self._store_email(foldername, input.filename, 'quagga.predicted', predicted)
			parsed = self._parse(predicted, input)
			self._store_email(foldername, input.filename, 'quagga.parsed', parsed)
		print("stored all stages in " + foldername)

	def store_input(self, foldername):
		self._store(foldername, 'quagga.input', self.emails_input)

	def store_predicted(self, foldername):
		self._store(foldername, 'quagga.predicted', self.emails_predicted())

	def store_parsed(self, foldername):
		self._store(foldername, 'quagga.parsed', self.emails_parsed())

	@staticmethod
	def _email_storage(input=None, predicted=None, parsed=None):
		return {'input': input,
		        'predicted': predicted,
		        'parsed': parsed}

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

	def _predict(self, mail_text):
		with self.graph.as_default():
			text_raw = mail_text
			text_lines = text_raw.split('\n')

			return self._prettify_prediction(*self.model.predict(text_lines))

	def _parse(self, email_prediction, email_input):
		return self.block_parser.parse_predictions(email_prediction, email_input)

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

	"""def print_predictions(self):
		for email_predicted in self.emails_predicted():
			for line_prediction in email_predicted:
				print(str(line_prediction['predictions']) + ' ' + line_prediction['text'])"""


if __name__ == '__main__':
	input_dir = "testMails"
	output_dir = "output"

	quagga = Quagga(EmailDirectoryReader(input_dir), output_dir=output_dir)

	"""print("========================= input ")
	for input in quagga.emails_input:
		pprint(input)
		
	print("========================= bodies ")
	for body in quagga.emails_body:
		pprint(body)

	print("========================= predictions ")
	for prediction in quagga.emails_predicted(input_reader=TempQuaggaReader('input', output_dir, output_func=lambda input: input['clean_body'])):
		pprint(prediction)

	print("========================= parsed ")
	for parsed in quagga.emails_parsed(prediction_reader=TempQuaggaReader('predicted', output_dir)):
		pprint(parsed)"""

	quagga.store_parsed(output_dir)
