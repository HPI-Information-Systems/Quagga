# -*- coding: utf-8 -*-

import numpy as np
import tensorflow as tf

from quaggaModelBuilder import QuaggaModelBuilder
from quaggaBlockParser import QuaggaBlockParser
from quaggaReader import QuaggaDirectoryReader, QuaggaListReaderRawEmailTexts, QuaggaListReaderExtractedBodies

from pprint import pprint


class Quagga:
	# todo block parser (refactoring)
	# todo block parser file format??
	def __init__(self):
		self.email_reader = None
		self.text_input = []
		self.emails_predicted = []
		self.emails_parsed = []

	def print_predictions(self):
		for email_predicted in self.emails_predicted:
			for line_prediction in email_predicted:
				print(str(line_prediction['predictions']) + ' ' + line_prediction['text'])

	def store_emails_predicted(self, filename):
		# todo store predictions
		# einmal dict zurückgeben
		# einfach das was rauskommt speichern
		# bisschen zusammenstellen was man haben mchte
		# json speichern
		pass

	def store_emails_parsed(self):
		# todo store parsed emails
		pass

	def read(self, email_reader):
		self.email_reader = email_reader
		self.email_bodies = [email.clean_body for email in self.email_reader]

	def predict(self, model_builder=QuaggaModelBuilder(), model=None):
		self.model_builder = model_builder
		if model is not None:
			self.model = model
		else:
			self.model_builder = model_builder
			self.model_builder.build()
			self.model = model_builder.quagga_model

		self.emails_predicted = [self._get_predictions(email_body) for email_body in self.email_bodies]

	def parse(self, block_parser=QuaggaBlockParser()):
		# todo add info from email protocol header to first block
		self.block_parser = block_parser
		for email_predicted in self.emails_predicted:
			blocks = self.block_parser.parse_predictions(email_predicted)
			self.emails_parsed.append(blocks)

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
		quagga.predict()
		quagga.parse()

		pprint(quagga.emails_parsed)

