# -*- coding: utf-8 -*-

import numpy as np
import tensorflow as tf
from quaggaModelBuilder import QuaggaModelBuilder
from quaggaBlockParser import QuaggaBlockParser

class Quagga:
	# todo block parser
	# todo store predictions
	def __init__(self, emails, model_builder=QuaggaModelBuilder(), block_parser=QuaggaBlockParser()):
		self.emails_input = emails

		self.model_builder = model_builder
		model_builder.build_configs()
		model_builder.build_models()
		self.model = model_builder.quagga_model

		self.block_parser = block_parser
		

	def print_predictions(self):
		for email_predicted in self.emails_predicted:
			for line_prediction in email_predicted:
				print(str(line_prediction['predictions']) + ' ' + line_prediction['text'])
	def store_predictions(self, filename):
		#todo
		pass

	def predict(self):
		self.emails_predicted = [self.get_predictions(email) for email in self.emails_input]
		
	def get_predictions(self, mail):
		text_raw = mail
		text_lines = text_raw.split('\n')

		return self.prettify_prediction(*self.model.predict(text_lines))
	        
	def prettify_prediction(self, y, text_lines, label_encoder):
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

	def parse(self):
		self.emails_parsed = self.block_parser.parse_predictions(self.emails_predicted)
		print(self.emails_parsed)


if __name__ == '__main__':
	
	emails = ['Daren:\n\
	\n\
	Just wanted to follow up with you on the April noms at Texas\n\
	City..............   the volumes recorded for April 1 were 5300 and 1165...\n\
	since we have been directed not to change Sitara deal tickets for now, would\n\
	you please correct?\n\
	\n\
	Thanks!!\n\
	\n\
	Charlotte\n\
	\n\
	---------------------- Forwarded by Charlotte Hawkins/HOU/ECT on 04/04/2000\n\
	01:37 PM ---------------------------\n\
	\n\
	\n\
	\n\
	From:  Charlotte Hawkins                           03/30/2000 11:33 AM\n\
	\n\
	\n\
	To: Daren J Farmer/HOU/ECT@ECT, Stacey Neuweiler/HOU/ECT@ECT\n\
	cc: Vance L Taylor/HOU/ECT@ECT, Mary Jo Johnson/HOU/ECT@ECT, Melissa\n\
	Graves/HOU/ECT@ECT\n\
	Subject: April, Aspect Volume @ Texas City\n\
	\n\
	\n\
	For April 1, 2000:\n\
	\n\
	Cross Media                         989815 =    903 MMBtu\n\
	TNCT                                      989816  = 5878  MMBtu\n\
	\n\
	Any questions, just call.\n\
	\n\
	Thanks,\n\
	\n\
	Charlotte Hawkins']

	quagga = Quagga(emails)
	quagga.predict()
	#quagga.print_predictions()
	quagga.parse()



"""
    - Klasse um alle emails einzulesen
    eingaben:
    - emails in textformat eingeben (später evtl auch einlesen)
    ausgaben:
    - blöcke zurückgeben
    - dieses format zurückgeben mit den regexes

    - eine klasse fürs parsing
    - eine klasse fürs model
    - models nicht alle auf einmal laden
    """












