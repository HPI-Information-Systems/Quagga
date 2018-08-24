from email import parser as ep
from datetime import datetime, timezone
import numpy as np
import os
import json

from Quagga.Utils.Email import EmailParser as Email

denotation_types = [
	"Header",
	"Header/Person",
	"Header/Person/From",
	"Header/Person/To",
	"Header/Person/Cc",
	"Header/Person/Bcc",
	"Header/Org",
	"Header/Org/From",
	"Header/Org/To",
	"Header/Org/Cc",
	"Header/Org/Bcc",
	"Header/Subject",
	"Header/Sent",
	"Header/Sent/Date",
	"Header/Sent/Time",
	"Body",
	"Body/Intro",
	"Body/Intro/Name",
	"Body/Outro",
	"Body/Outro/Name",
	"Body/Attachments",
	"Body/Attachments/Attachment",
	"Body/PS",
	"Body/Signature",
	"Body/Signature/Name",
	"Body/Signature/Position",
	"Body/Signature/Mail",
	"Body/Signature/Phone",
	"Body/Signature/Fax",
	"Body/Signature/Organisation",
	"Body/Signature/Address",
	"Body/Signature/Disclaimer"
]

relation_types = {
	"Alias": {
		"type": "symmetric-transitive"
	},
	"ContactInfo": {
		"type": "directed"
	},
	"WorksFor": {
		"type": "directed"
	},
	"BelongsTo": {
		"type": "directed"
	}
}


def _overlap(denotation, line):
	if denotation['start'] >= line['end'] or denotation['end'] <= line['start']:
		return 0.0
	if denotation['start'] <= line['start'] and denotation['end'] >= line['end']:
		return 1.0
	if denotation['start'] >= line['start'] and denotation['end'] <= line['end']:
		return (denotation['end'] - denotation['start']) / (line['end'] - line['start'])
	if line['start'] < denotation['start'] < line['end']:
		return (line['end'] - denotation['start']) / (line['end'] - line['start'])
	if denotation['start'] < line['start'] < denotation['end']:
		return (denotation['end'] - line['start']) / (line['end'] - line['start'])


def _labels_to_numeric(labels):
	return [denotation_types.index(l) for l in labels]


class AnnotatedEmail(Email):
	def __init__(self, file, skip_blank=False, perturbation=0.0):
		self.skip_blank = skip_blank
		self.perturbation = perturbation
		try:
			f = open(file, 'r')
			self.annotation = json.load(f)
			f.close()
			super().__init__(os.path.dirname(file), os.path.basename(file), self.annotation['meta'].get('header', {}))
		except json.decoder.JSONDecodeError:
			print('Error loading JSON Annotation File: ' + file)
			raise

	@property
	def body(self):
		return self.annotation['text']

	@property
	def lines(self):
		# return [l+'\n' for l in self.body.split('\n') if not (self.skip_blank and re.search(r"^\s*$", l))]
		return [self._perturbate_line(l) + '\n' for l in self.body.split('\n')]

	@property
	def lines_clean(self):
		# return [l+'\n' for l in self.body.split('\n') if not (self.skip_blank and re.search(r"^\s*$", l))]
		return [l + '\n' for l in self.body.split('\n')]

	def _perturbate_line(self, line):
		if self.perturbation < 0.001:
			return line
		ret = ''
		chars = list(' '
		             'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
		             'abcdefghijklmnopqrstuvwxyz'
		             '0123456789'
		             '@€-_.:,;#\'+*~\?}=])[({/&%$§"!^°|><´`')
		rem = 0.33 * self.perturbation
		add = 0.66 * self.perturbation
		randoms = np.random.rand(len(line))
		for i, rand in enumerate(randoms):
			if rand > self.perturbation:
				ret += line[i]
			else:
				if rand < rem:
					# remove character
					pass
				elif rand < add:
					# add character
					ret += line[i]
					ret += chars[np.random.randint(0, len(chars), 1)[0]]
				else:
					# edit character
					ret += chars[np.random.randint(0, len(chars), 1)[0]]
		return ret

	def __len__(self):
		return len(self.lines)

	@property
	def lines_with_boundaries(self):
		lines = self.lines_clean
		cursor = 0
		ret = []
		for line in lines:
			ret.append({'start': cursor, 'end': cursor + len(line), 'text': line})
			cursor += len(line)
		return ret

	@property
	def denotations(self):
		return self.annotation['denotations']

	@property
	def relations(self):
		return self.annotation['relations']

	@property
	def two_zones_labels(self):
		return self._line_labels(zones=2)

	@property
	def three_zones_labels(self):
		return self._line_labels(zones=3)

	@property
	def five_zones_labels(self):
		return self._line_labels(zones=5)

	@property
	def two_zones_labels_numeric(self):
		return _labels_to_numeric(self.two_zones_labels)

	@property
	def three_zones_labels_numeric(self):
		return _labels_to_numeric(self.three_zones_labels)

	@property
	def five_zones_labels_numeric(self):
		return _labels_to_numeric(self.five_zones_labels)

	def _denotation_overlaps(self, limit=None):
		lines = self.lines_with_boundaries
		denotations = self.denotations
		ret = []
		for line in lines:
			l = {}
			for denotation in denotations:
				if limit is not None and denotation['type'] not in limit:
					continue
				o = _overlap(denotation, line)
				if o > 0:
					l[denotation['type']] = o
					# print(line['start'], line['end'], denotation['type'], denotation['start'], denotation['end'], o)
			if len(l.keys()) == 0:
				l['Body'] = 1.0
			ret.append(sorted(l.items(), key=lambda i: i[1], reverse=True))
		return ret

	@staticmethod
	def zone_labels(zones=2):
		limit = None
		if zones == 2:
			limit = ['Body', 'Header']
		elif zones == 3:
			limit = ['Body', 'Header', 'Body/Signature']
		elif zones == 5:
			limit = ['Body', 'Header', 'Body/Signature', 'Body/Intro', 'Body/Outro']
		return limit

	def _line_labels(self, zones=2):
		limit = self.zone_labels(zones)
		overlaps = self._denotation_overlaps(limit)
		return [overlap[0][0] for overlap in overlaps]


class AnnotatedEmails:
	def __init__(self, folder, feature_function, skip_blank=False, perturbation=0.0):
		self.skip_blank = skip_blank  # TODO
		self.feature_function = feature_function
		self.perturbation = perturbation
		self.emails_train = []
		self.emails_test = []
		self.emails_eval = []

		for root, _, files in os.walk(folder):
			for file in files:
				if file.endswith('.ann'):
					fname = os.path.join(root, file)
					if 'eval' in fname:
						self.emails_eval.append(AnnotatedEmail(fname, skip_blank, perturbation=self.perturbation))
					elif 'test' in fname:
						self.emails_test.append(AnnotatedEmail(fname, skip_blank, perturbation=self.perturbation))
					else:
						self.emails_train.append(AnnotatedEmail(fname, skip_blank, perturbation=self.perturbation))
		print('train:', len(self.emails_train))
		print('test', len(self.emails_test))
		print('eval:', len(self.emails_eval))

	@property
	def train_set(self):
		return self.emails_train

	@property
	def test_set(self):
		return self.emails_test

	@property
	def eval_set(self):
		return self.emails_eval

	@property
	def full_set(self):
		return self.train_set + self.test_set + self.eval_set

	@property
	def features(self):
		return ([self.feature_function(m) for m in self.train_set],
		        [self.feature_function(m) for m in self.test_set],
		        [self.feature_function(m) for m in self.eval_set])

	@property
	def features_full(self):
		return [self.feature_function(m) for m in self.full_set]

	@property
	def two_zones_labels(self):
		return ([m.two_zones_labels for m in self.train_set],
		        [m.two_zones_labels for m in self.test_set],
		        [m.two_zones_labels for m in self.eval_set])

	@property
	def two_zones_labels_full(self):
		return [m.two_zones_labels for m in self.full_set]

	@property
	def two_zones_labels_numeric(self):
		return ([m.two_zones_labels_numeric for m in self.train_set],
		        [m.two_zones_labels_numeric for m in self.test_set],
		        [m.two_zones_labels_numeric for m in self.eval_set])

	@property
	def two_zones_labels_numeric_full(self):
		return [m.two_zones_labels_numeric for m in self.full_set]

	@property
	def three_zones_labels(self):
		return ([m.three_zones_labels for m in self.train_set],
		        [m.three_zones_labels for m in self.test_set],
		        [m.three_zones_labels for m in self.eval_set])

	@property
	def three_zones_labels_full(self):
		return [m.three_zones_labels for m in self.full_set]

	@property
	def three_zones_labels_numeric(self):
		return ([m.three_zones_labels_numeric for m in self.train_set],
		        [m.three_zones_labels_numeric for m in self.test_set],
		        [m.three_zones_labels_numeric for m in self.eval_set])

	@property
	def three_zones_labels_numeric_full(self):
		return [m.three_zones_labels_numeric for m in self.full_set]

	@property
	def five_zones_labels(self):
		return ([m.five_zones_labels for m in self.train_set],
		        [m.five_zones_labels for m in self.test_set],
		        [m.five_zones_labels for m in self.eval_set])

	@property
	def five_zones_labels_full(self):
		return [m.five_zones_labels for m in self.full_set]

	@property
	def five_zones_labels_numeric(self):
		return ([m.five_zones_labels_numeric for m in self.train_set],
		        [m.five_zones_labels_numeric for m in self.test_set],
		        [m.five_zones_labels_numeric for m in self.eval_set])

	@property
	def five_zones_labels_numeric_full(self):
		return [m.five_zones_labels_numeric for m in self.full_set]


class AnnotatedEmailsIterator:
	def __init__(self, folder):
		self.folder = folder

	def _iterator(self, split):
		for root, _, files in os.walk(self.folder):
			for file in files:
				if file.endswith('.ann'):
					fname = os.path.join(root, file)
					if split in fname:
						yield AnnotatedEmail(fname, False)

	@property
	def test(self):
		return self._iterator('test')

	@property
	def eval(self):
		return self._iterator('eval')

	@property
	def train(self):
		return self._iterator('train')
