import re
from datetime import datetime, timezone


class Email:
	def __dict__(self):
		return {
			'sent': self.sent,
			'file': self.file,
			'folder': self.folder,
			'id': self.id,
			'mailbox': self.mailbox,
			'subject': self.subject,
			'sender': self.sender,
			'xsender': self.xsender,
			'to': self.to,
			'xto': self.xto,
			'cc': self.cc,
			'xcc': self.xcc,
			'bcc': self.bcc,
			'xbcc': self.xbcc,
			'body': self.body,
			'clean_body': self.clean_body
		}

	@property
	def sent(self):
		return ''

	@property
	def file(self):
		return ''

	@property
	def folder(self):
		return ''

	@property
	def id(self):
		return ''

	@property
	def mailbox(self):
		return ''

	@property
	def subject(self):
		return ''

	@property
	def sender(self):
		return ''

	@property
	def xsender(self):
		return ''

	@property
	def to(self):
		return ''

	@property
	def xto(self):
		return ''

	@property
	def cc(self):
		return ''

	@property
	def xcc(self):
		return ''

	@property
	def bcc(self):
		return ''

	@property
	def xbcc(self):
		return ''

	@property
	def body(self):
		return ''

	@property
	def clean_body(self):
		return ''


class EmailMessage(Email):
	def __init__(self, path, filename, mail):
		self.path = path
		self.filename = filename
		self.mail = mail

	@property
	def sent(self):
		return datetime.strptime(re.sub(r' *\([A-Z]+\)', '', str(self.mail['Date'])),
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
	def header(self):
		return ''

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


class EmailBody(Email):
	def __init__(self, body_text):
		self.body_text = body_text

	@property
	def body(self):
		return self.body_text

	@property
	def clean_body(self):
		return self.body_text



def serialize_quagga_email(obj):
	"""JSON serializer for objects not serializable by default json code"""

	if isinstance(obj, Email):
		serial = obj.__dict__()
		return serial
