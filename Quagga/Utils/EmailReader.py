from email import parser as ep
import os
import json

from Utils.Email import EmailMessage, EmailBody


class DirectoryIterator:
	def __init__(self, maildir, limit=None, skip=0, file_func=lambda _: True, reader_func=lambda path, filename, file: (path, filename, file)):
		self.run = 0
		self.limit = limit
		self.skip = skip
		self.file_func = file_func
		self.reader_func = reader_func

		self.maildir = maildir

		self.os_walker = os.walk(self.maildir)
		self.current_dirs = []
		self.current_files = iter([])
		self.current_root_dir = ''


		for i in range(self.skip):
			self.run += 1
			self._next_file(skipmode=True)

	@property
	def current_root_dir_stripped(self):
		return self.current_root_dir[len(self.maildir):]

	def _next_file(self, skipmode=False):
		try:
			filename = next(self.current_files)

			if not self.file_func(filename):
				return self._next_file()


			# save some effort when result is dumped anyway during skip-ahead
			if not skipmode:
				with open(self.current_root_dir + "/" + filename, "r", errors='ignore') as f:
					self.run += 1
					file = f.read() # todo read on client side so you can avoid it if not needed

					return self.current_root_dir_stripped, filename, file
		except StopIteration:
			self._next_dir()
			return self._next_file()


	def _next_dir(self):
		self.current_root_dir, self.current_dirs, files = next(self.os_walker)
		if len(files) > 0:
			self.current_files = iter(files)
		else:
			self._next_dir()

	def __next__(self):
		if self.limit is not None and (self.limit + self.skip) <= self.run:
			raise StopIteration()

		return self.reader_func(*self._next_file())

class DirectoryReader:
	def __init__(self, maildir, limit=None, skip=0, file_func=lambda filename: True, output_func=lambda path, filename, file: (path, filename, file)):
		self.maildir = maildir
		self.limit = limit
		self.skip = skip
		self.file_func = file_func
		self._file_func = lambda filename: '.DS_Store' not in filename and self.file_func(filename)
		self.email_func = output_func

	def __iter__(self):
		return DirectoryIterator(self.maildir, self.limit, self.skip, self._file_func, self.email_func)

class TempQuaggaReader(DirectoryReader):
	def __init__(self, stage, maildir, limit=None, skip=0, output_func=lambda x:x):
		super().__init__(maildir, limit, skip)
		self.stage = stage
		self.file_func = lambda filename: self.stage in filename
		self.email_func = lambda path, filename, file: output_func(json.loads(file)['quagga.' + self.stage])


class EmailDirectoryReader(DirectoryReader):
	def __init__(self, maildir, limit=None, skip=0):
		super().__init__(maildir, limit, skip)
		self.email_parser = ep.Parser()
		self.file_func = lambda filename: '.quagga.' not in filename
		self.email_func = lambda path, filename, file: EmailMessage(path, filename, self.email_parser.parsestr(file))




class ListReaderExtractedBodies:
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


class ListReaderRawEmailTexts():
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
		return EmailMessage(None, None, self.mail_parser.parsestr(raw_text))


if __name__ == '__main__':

	test_dir = "testMails"

	with open(test_dir + "/bass-e__sent_mail_20.txt", "r", errors='ignore') as f:
		print("==============================")
		for email in EmailDirectoryReader('testMails'):
			print(email.clean_body)

		print("==============================")
		raw_email = [f.read()]
		for email in ListReaderRawEmailTexts(raw_email):
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
		for email in ListReaderExtractedBodies(body):
			print(email.clean_body)
