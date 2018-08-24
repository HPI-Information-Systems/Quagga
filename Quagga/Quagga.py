#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-


from Quagga.Utils.ModelBuilder import ModelBuilder
from Quagga.Utils.BlockParser import BlockParser
from Quagga.Utils.EmailReader import DirectoryReader, EmailDirectoryReader, TempQuaggaReader, ListReaderRawEmailTexts, \
	ListReaderExtractedBodies
from Quagga.Utils.Email import Email, serialize_quagga_email
from Quagga.Utils.EmailProcessor import EmailProcessor

import tensorflow as tf
from pprint import pprint
import json
from enum import IntEnum

import os


class State(IntEnum):
	INIT = 0
	PREDICT = 1
	PARSE = 2


class Quagga:

	def __init__(self, email_reader, output_dir, model_builder=ModelBuilder(), model=None,
	             block_parser=BlockParser()):

		self.state = State.INIT

		self.output_dir = output_dir

		self._INPUT = 'quagga.input'
		self._PREDICTED = 'quagga.predicted'
		self._PARSED = 'quagga.parsed'

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
		return EmailProcessor(self, self.emails_input, self.output_dir, self.emails_input, lambda email, _: email.clean_body, self._INPUT, State.INIT)

	def emails_predicted(self, input_reader=None):  # todo use decorator for tempReaders
		if self.state >= State.PREDICT:
			return TempQuaggaReader(self._PREDICTED, self.output_dir)
		if input_reader is None:
			input_reader = self.emails_body
		else:
			print("reading bodies from .quagga files...")

		return EmailProcessor(self, self.emails_input, self.output_dir, input_reader,
		                      lambda email_body, _: self._predict(email_body), self._PREDICTED, State.PREDICT)

	def emails_parsed(self, prediction_reader=None):
		if self.state >= State.PARSE:
			return TempQuaggaReader(self._PARSED, self.output_dir)
		if prediction_reader is None:
			prediction_reader = self.emails_predicted()
		else:
			print("reading predictions from .quagga files...")
		return EmailProcessor(self, self.emails_input, self.output_dir, prediction_reader,
		                      lambda email_prediction, email_input: self._parse(
			                      email_prediction, email_input), self._PARSED, State.PARSE)




	# this is optimized so things are loaded only once into memory and not written and read from disk immediately after
	def store_all(self, foldername):
		for input in self.emails_input:
			self._store_email(foldername, input.filename, self._INPUT, input)
			predicted = self._predict(input.clean_body)
			self._store_email(foldername, input.filename, self._PREDICTED, predicted)
			parsed = self._parse(predicted, input)
			self._store_email(foldername, input.filename, self._PARSED, parsed)
		print("stored all stages in " + foldername)

	def store_input(self, foldername):
		self._store(foldername, self._INPUT, self.emails_input)

	def store_predicted(self, foldername):
		self._store(foldername, self._PREDICTED, self.emails_predicted())

	def store_parsed(self, foldername):
		self._store(foldername, self._PARSED, self.emails_parsed())

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
	input_dir = "test/testData"
	output_dir = input_dir + "/output"

	quagga = Quagga(EmailDirectoryReader(input_dir), output_dir)

	print("========================= input ")
	for input in quagga.emails_input:
		pprint(input)
		
	print("========================= bodies ")
	for body in quagga.emails_body:
		pprint(body)

	print("========================= predictions ")
	for prediction in quagga.emails_predicted(input_reader=TempQuaggaReader('quagga.input', output_dir, output_func=lambda input: input['clean_body'])):
		pprint(prediction)

	print("========================= parsed ")
	for parsed in quagga.emails_parsed(prediction_reader=TempQuaggaReader('quagga.predicted', output_dir)):
		pprint(parsed)

	quagga.store_parsed(output_dir)
