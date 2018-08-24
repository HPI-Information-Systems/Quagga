# -*- coding: utf-8 -*-

import keras.backend as K
from keras_contrib.utils import save_load_utils
from keras.models import model_from_json
from keras.models import Model as KerasModel
from keras.layers import Masking, GRU, Input, Bidirectional
from keras_contrib.layers import CRF
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
import os.path
from pkg_resources import resource_filename


from Quagga.Utils.Model import Model as QuaggaModel

def get_relative_filename(file):
	dirname = os.path.dirname(__file__)
	filename = os.path.join(dirname, file)
	return filename

def get_resource_string(file):

	#return get_relative_filename(file)
	return resource_filename(__name__, file)


class ModelBuilder:

	# todo model trainieren

	def __init__(self, with_crf=True, zones=2, trainset='enron'):

		if zones not in [2, 5]:
			raise ValueError('Only trained for 2 and 5 zone predictions!')
		if trainset not in ['enron', 'asf']:
			raise ValueError("Only trained on 'enron' and 'asf' corpus!")
		if with_crf not in [True, False]:
			raise ValueError("Invalid value for with_crf. Has to be bool!")

		self.line_embedding_size = 32

		# todo use @dataclass ?
		self.model_paths = {}

		self.zones = zones
		self.trainset = trainset
		self.with_crf = with_crf

		self.quagga_model = QuaggaModel()

		if self.zones == 5:
			if self.trainset == 'enron':
				self.model_paths['line_a_path'] = get_resource_string('models/five_zones/enron_line_model_a')
				self.model_paths['line_b_path'] = get_resource_string('models/five_zones/enron_line_model_b')
				self.model_paths['model_path'] = get_resource_string('models/five_zones/enron_model')
			elif self.trainset == 'asf':
				self.model_paths['line_a_path'] = get_resource_string('models/five_zones/asf_line_model_a')
				self.model_paths['line_b_path'] = get_resource_string('models/five_zones/asf_line_model_b')
				self.model_paths['model_path'] = get_resource_string('models/five_zones/asf_model')

		elif self.zones == 2:
			if self.trainset == 'enron':
				self.model_paths['line_b_path'] = get_resource_string('models/two_zones/enron_line_model_b')
				self.model_paths['model_path'] = get_resource_string('models/two_zones/enron_model')
			elif self.trainset == 'asf':
				self.model_paths['line_b_path'] = get_resource_string('models/two_zones/asf_line_model_b')
				self.model_paths['model_path'] = get_resource_string('models/two_zones/asf_model')

	@classmethod
	def from_paths_two_zones(cls, model_path, line_b_path):
		inst = cls()
		inst.model_paths['model_path'] = model_path
		inst.model_paths['line_b_path'] = line_b_path

		inst.zones = 2
		inst.trainset = 'own trainset provided'
		return inst

	@classmethod
	def from_paths_five_zones(cls, model_path, line_b_path, line_a_path):
		inst = cls()
		inst.model_paths['model_path'] = model_path
		inst.model_paths['line_b_path'] = line_b_path
		inst.model_paths['line_a_path'] = line_a_path

		inst.zones = 5
		inst.trainset = 'own trainset provided'
		return inst

	def build(self):
		self._build_configs()
		self._build_model()
		self._build_line_model()


	def _build_configs(self):
		self.quagga_model.zones = self.zones
		self.quagga_model.with_crf = self.with_crf
		self.quagga_model.trainset = self.trainset

		if self.zones == 2:
			self.quagga_model.encoder = LabelEncoder().fit(['Body', 'Header'])
		elif self.zones == 5:
			self.quagga_model.encoder = LabelEncoder().fit(
				['Body', 'Header', 'Body/Signature', 'Body/Intro', 'Body/Outro'])

	def _build_model(self):
		self.quagga_model.model = self._load_keras_model(self.model_paths['model_path'], self._mail_model)

	def _build_line_model(self):
		line_model_b = self._load_keras_model(self.model_paths['line_b_path'])
		line_b_func = self._get_embedding_function(line_model_b)

		if self.zones == 2:
			line_model = line_model_b
			line_funcs = [line_b_func]
		elif self.zones == 5:
			line_model = self._load_keras_model(self.model_paths['line_a_path'])
			line_a_func = self._get_embedding_function(line_model)
			line_funcs = [line_a_func, line_b_func]

		self.quagga_model.line_model = line_model
		self.quagga_model.line_functions = line_funcs

	@property
	def _mail_model(self):
		if self.zones == 2:
			return self._mail_model_two
		elif self.zones == 5:
			return self._mail_model_five

	def _load_keras_model(self, path, model=None):
		with open(os.path.abspath(path + '.json'), 'r') as jf:
			json_model = jf.read()
		if model is None:
			model = model_from_json(json_model)
		# model.summary()
		# print(model.get_weights()[0])
		try:
			save_load_utils.load_all_weights(model, os.path.abspath(path + '.hdf5'))
		except KeyError:
			model.load_weights(os.path.abspath(path + '.hdf5'))
		# print(model.get_weights()[0])
		return model

	def _get_embedding_function(self, model):
		model_in = [model.input]
		embedding_func = K.function(model_in + [K.learning_phase()], [model.layers[-2].output])

		def lambdo(x):
			return embedding_func([x, 0.])[0]

		return lambdo

	@property
	def _mail_model_five(self):
		output_size = 5
		in_mail = Input(shape=(None, self.line_embedding_size * 2), dtype='float32')
		mask = Masking()(in_mail)
		hidden = GRU(32,
		             return_sequences=True,
		             implementation=0)(mask)
		crf = CRF(output_size, sparse_target=False)
		output = crf(hidden)

		model = KerasModel(inputs=in_mail, outputs=output)
		# model.compile(loss=crf.loss_function, optimizer='adam', metrics=[crf.accuracy])
		return model

	@property
	def _mail_model_two(self):
		output_size = 2
		in_mail = Input(shape=(None, self.line_embedding_size), dtype='float32')

		mask = Masking()(in_mail)
		hidden = Bidirectional(GRU(32 // 2,
		                           return_sequences=True,
		                           implementation=0))(mask)
		crf = CRF(output_size, sparse_target=False)  # , test_mode='marginal', learn_mode='marginal')
		output = crf(hidden)

		model = KerasModel(inputs=in_mail, outputs=output)
		# model.compile(loss=crf.loss_function, optimizer='adam', metrics=[crf.accuracy])
		return model
