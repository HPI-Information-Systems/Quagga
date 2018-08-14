from email import parser as ep
from datetime import datetime, timezone
import os
import re


class Email:
	@property
	def sent(self):
		pass

	@property
	def file(self):
		pass

	@property
	def folder(self):
		pass

	@property
	def id(self):
		pass

	@property
	def mailbox(self):
		pass

	@property
	def subject(self):
		pass

	@property
	def sender(self):
		pass

	@property
	def xsender(self):
		pass

	@property
	def to(self):
		pass

	@property
	def xto(self):
		pass

	@property
	def cc(self):
		pass

	@property
	def xcc(self):
		pass

	@property
	def bcc(self):
		pass

	@property
	def xbcc(self):
		pass

	@property
	def body(self):
		pass

	@property
	def clean_body(self):
		pass


class EmailBody(Email):
	def __init__(self, body_text):
		self.body_text = body_text

	@property
	def body(self):
		return self.body_text

	@property
	def clean_body(self):
		return self.body_text


class EmailParser(Email):
	def __init__(self, path, filename, mail):
		self.path = path
		self.filename = filename
		self.mail = mail

	@property
	def sent(self):
		return datetime.strptime(re.sub(r' *\([A-Z]+\)', '', self.mail['Date']),
		                         '%a, %d %b %Y %H:%M:%S %z').astimezone(timezone.utc)

	@property
	def file(self):
		return self.path + '/' + self.filename

	@property
	def folder(self):
		return '/'.join(self.path.split('/')[1:])

	@property
	def id(self):
		return self.mail.get('Message-ID', '')

	@property
	def mailbox(self):
		return self.mail.get('X-Origin', '')

	@property
	def subject(self):
		return self.mail.get('Subject', '')

	@property
	def sender(self):
		return self.mail.get('From', '')

	@property
	def xsender(self):
		return self.mail.get('X-From', '')

	@property
	def to(self):
		return self.mail.get('To', '')

	@property
	def xto(self):
		return self.mail.get('X-To', '')

	@property
	def cc(self):
		return self.mail.get('Cc', '')

	@property
	def xcc(self):
		return self.mail.get('X-cc', '')

	@property
	def bcc(self):
		return self.mail.get('Bcc', '')

	@property
	def xbcc(self):
		return self.mail.get('X-bcc', '')

	@property
	def body(self):
		return self.mail.get_payload()

	@property
	def clean_body(self):
		s = self.body

		# remove annotation (if present)
		s = re.sub("^(H|S|B)>", "", s, flags=re.M)

		# remove known common rubbish
		s = s.replace('=\n', '').replace('=20', '').replace('=09', '').replace('=01\&', '') \
			.replace('=01&', '').replace('=18', '').replace('=018', '')

		# remove indentation
		# s = re.sub(r"^(\s*>)+","", s)

		# remove attachments
		s = re.sub(r"\s*\[IMAGE\]\s*", "", s, flags=re.I)
		s = re.sub(r"<<.{3,50}\.(xls|xlsx|png|gif|jpg|jpeg|doc|docx|ppt|pptx|pst)>>%?", "", s, flags=re.I)
		s = re.sub(r"^\s*-.{3,50}\.(xls|xlsx|png|gif|jpg|jpeg|doc|docx|ppt|pptx|pst)%?", "", s, flags=re.I)
		return s


class EmailFiles:
	def __init__(self, maildir, limit=None, skip=0):
		self.maildir = maildir
		self.limit = limit
		self.current_root_dir = ''
		self.skip = skip

	def __iter__(self):
		self.run = 0
		self.os_walker = os.walk(self.maildir)
		self.current_dirs = []
		self.current_files = iter([])

		for i in range(self.skip):
			self.run += 1
			self._next_file(skipmode=True)
		return self

	@property
	def current_root_dir_stripped(self):
		return self.current_root_dir[len(self.maildir):]

	def _next_dir(self):
		self.current_root_dir, self.current_dirs, files = next(self.os_walker)
		if len(files) > 0:
			self.current_files = iter(files)
		else:
			self._next_dir()

	def _next_file(self, skipmode=False):
		try:
			filename = next(self.current_files)

			if filename == '.DS_Store': # todo there has got to be a better way
				return self._next_file()

			# save some effort when result is dumped anyway during skip-ahead
			if not skipmode:
				with open(self.current_root_dir + "/" + filename, "r", errors='ignore') as f:
					self.run += 1
					file = f.read()

					# must be something off here, skipping
					if len(file) < 100:
						return self._next_file()

					return self.current_root_dir_stripped, filename, file
		except StopIteration:
			self._next_dir()
			return self._next_file()

	def __next__(self):
		if self.limit is not None and (self.limit + self.skip) <= self.run:
			raise StopIteration()

		return self._next_file()


class QuaggaListReaderExtractedBodies:  # null object
	def __init__(self, body_texts):
		self.body_texts = body_texts

	def __iter__(self):
		self.index = -1
		return self

	def __next__(self):
		self.index += 1
		if self.index >= len(self.body_texts):
			raise StopIteration
		return EmailBody(self.body_texts[self.index])


class QuaggaListReaderRawEmailTexts():
	def __init__(self, raw_texts):
		self.mail_parser = ep.Parser()
		self.raw_texts = raw_texts

	def __iter__(self):
		self.raw_texts_iter = iter(self.raw_texts)
		return self

	def __next__(self):
		try:
			raw_text = self.raw_texts_iter.__next__()
		except StopIteration:
			raise StopIteration
		return EmailParser(None, None, self.mail_parser.parsestr(raw_text))


class QuaggaDirectoryReader(EmailFiles):
	def __init__(self, maildir, limit=None, skip=0):
		super().__init__(maildir, limit, skip)
		self.mail_parser = ep.Parser()

	def __next__(self):
		path, filename, file = super().__next__()
		return EmailParser(path, filename, self.mail_parser.parsestr(file))


if __name__ == '__main__':

	test_dir = "testMails"

	with open(test_dir + "/bass-e__sent_mail_20.txt", "r", errors='ignore') as f:
		print("==============================")
		for email in QuaggaDirectoryReader('testMails'):
			print(email.clean_body)

		print("==============================")
		raw_email = [f.read()]
		for email in QuaggaListReaderRawEmailTexts(raw_email):
			print(email.clean_body)

		print("==============================")
		body = ["That's it.  Thanks to plove I am no longer entering my own deals.\n\
\n\
\n\
\n\
		Phillip M Love\n\
03/26/2001 10:20 AM\n\
To:	Eric Bass/HOU/ECT@ECT\n\
cc:	 \n\
Subject:	Re:   \n\
	\n\
We can always count on you to at least give us one on the error report.\n\
PL\n\
\n\
\n\
        < Embedded StdOleLink >"]
		for email in QuaggaListReaderExtractedBodies(body):
			print(email.clean_body)
