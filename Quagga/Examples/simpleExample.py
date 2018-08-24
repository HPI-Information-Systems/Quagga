#!/usr/bin/env python3.6

from pprint import pprint

from Quagga import Quagga
from Quagga import EmailDirectoryReader, ListReaderRawEmailTexts, ListReaderExtractedBodies, TempQuaggaReader

from Quagga.Utils.ModelBuilder import ModelBuilder
from Quagga.Utils.BlockParser import BlockParser

import os.path

example_email_raw = "Message-ID: <20646012.1075840326283.JavaMail.evans@thyme>\n\
Date: Mon, 26 Mar 2001 13:33:00 -0800 (PST)\n\
From: eric.bass@enron.com\n\
To: phillip.love@enron.com\n\
Subject: Re:\n\
Cc: chance.rabon@enron.com, david.baumbach@enron.com, o'neal.winfree@enron.com\n\
Mime-Version: 1.0\n\
Content-Type: text/plain; charset=us-ascii\n\
Content-Transfer-Encoding: 7bit\n\
Bcc: chance.rabon@enron.com, david.baumbach@enron.com, o'neal.winfree@enron.com\n\
X-From: Eric Bass\n\
X-To: Phillip M Love <Phillip M Love/HOU/ECT@ECT>\n\
X-cc: Chance Rabon <Chance Rabon/ENRON@enronXgate>, David Baumbach <David Baumbach/HOU/ECT@ECT>, O'Neal D Winfree <O'Neal D Winfree/HOU/ECT@ECT>\n\
X-bcc: \n\
X-Folder: \ExMerge - Bass, Eric\'Sent Mail\n\
X-Origin: BASS-E\n\
X-FileName: eric bass 6-25-02.PST\n\
\n\
That's it.  Thanks to plove I am no longer entering my own deals.\n\
\n\
\n\
\n\
\n\
From:	Phillip M Love\n\
03/26/2001 10:20 AM\n\
To:	Eric Bass/HOU/ECT@ECT\n\
cc:	\n\
Subject:	Re:   \n\
\n\
We can always count on you to at least give us one on the error report.\n\
PL\n\
\n\
\n\
\n\
\n\
\n\
<Embedded StdOleLink>"

example_email_body = "That's it.  Thanks to plove I am no longer entering my own deals.\n\
\n\
\n\
\n\
\n\
From:	Phillip M Love\n\
03/26/2001 10:20 AM\n\
To:	Eric Bass/HOU/ECT@ECT\n\
cc:	\n\
Subject:	Re:   \n\
\n\
We can always count on you to at least give us one on the error report.\n\
PL\n\
\n\
\n\
\n\
\n\
\n\
<Embedded StdOleLink>"

def get_relative_filename(file):
	dirname = os.path.dirname(__file__)
	filename = os.path.join(dirname, file)
	return filename

input_dir = get_relative_filename("testData")
output_dir = input_dir + "/output"



"""
Quagga requires an Iterator over Quagga.Utils.Email.EmailMessage as input
Quagga requires an output directory where prediction results are stored (api reasons, maybe tmp files)
"""

# read email bodies from text
quagga = Quagga(ListReaderExtractedBodies([example_email_body]), output_dir) # you obviously can't store these mails on disk, they don't have a filename

# read emails from raw text
quagga = Quagga(ListReaderRawEmailTexts([example_email_raw]), output_dir)

# read all emails from a directory
quagga = Quagga(EmailDirectoryReader(input_dir), output_dir)



"""
Quagga can be configured with your own model, model_builder or block_parser.
"""
quagga = Quagga(EmailDirectoryReader(input_dir), output_dir, model_builder=ModelBuilder(), model=None,
	             block_parser=BlockParser())



print("========================= input ")
"""Quagga.Utils.Email.EmailMessage. Contains raw email and parsed metadata."""
for input in quagga.emails_input:
	pprint(input)

print("========================= bodies ")
"""String. Contains body from Quagga.Utils.Email.EmailMessage."""
for body in quagga.emails_body:
	pprint(body)

print("========================= predictions ")
"""Dictionary. Contains predictions line by line."""
for prediction in quagga.emails_predicted():
	pprint(prediction)

print("========================= parsed ")
"""Dictionary. Contains semi-structured data extracted from email."""
for parsed in quagga.emails_parsed():
	pprint(parsed)


"""
Store stuff for each email on disk.
"""
quagga.store_input(output_dir)
quagga.store_predicted(output_dir)
quagga.store_parsed(output_dir)

quagga.store_all(output_dir)


"""
Reuse already done work, don't predict everything again but read from files
You have to make sure that .input. and .predicted. files are up-to-date.
"""
print("========================= predictions ")
for prediction in quagga.emails_predicted(input_reader=TempQuaggaReader('quagga.input', output_dir, output_func=lambda input: input['clean_body'])):
	pprint(prediction)

print("========================= parsed ")
for parsed in quagga.emails_parsed(prediction_reader=TempQuaggaReader('quagga.predicted', output_dir)):
	pprint(parsed)


