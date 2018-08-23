import re


class BlockParser:


	def _top_prediction(self, predictions):
		return sorted(predictions.items(), key=lambda x: x[1], reverse=True)[0][0]

	def _add_header_info(self, blocks, email_raw_parser):
		if len(blocks) > 0:
			root_message = blocks[0]
			root_message['from'] = email_raw_parser.sender
			root_message['to'] = email_raw_parser.to
			root_message['cc'] = email_raw_parser.cc
			#root_message['sent'] = email_raw_parser.sent.strftime("%Y-%m-%d %H:%M:%S") #todo
			root_message['subject'] = email_raw_parser.subject
		# todo raw_header

	def parse_predictions(self, email_predicted, email_input):

		blocks = []
		# pre-filled info comes from email protocol header
		curr_block = {
			'from': 'dummy@from.com',
			'to': 'dummy@to.com',
			'cc': 'dummy@cc.com',
			'sent': '01/01/2000 12:12 PM',
			'subject': 'Dummy Subject',
			'type': 'root',  # root, forward, reply
			'raw_header': [],
			'text': []
		}
		# modes: 0 = eat body, 1 = eat forward, 2 = eat reply,
		#        3 = eat from, 4 = eat to, 5 = eat cc/bcc, 6 = sent, 7 = eat subject
		mode = 0
		for line_prediction in email_predicted:
			top_prediction = self._top_prediction(line_prediction['predictions'])
			line_low = line_prediction['text'].lower()
			if top_prediction == 'Header':
				# looks like the root block ends here...
				if mode == 0:
					blocks.append(curr_block)
					next_mode = 1 if 'forward' in line_low else 2
					curr_block = {'from': None, 'to': None, 'cc': None, 'sent': None, 'subject': None,
					              'type': 'forward' if next_mode == 1 else 'reply',
					              'raw_header': [],
					              'text': []}
					mode = next_mode

				# stop eating forward header when seeing "-----Original Message-----"
				if mode == 1 and 'original' in line_low:
					blocks.append(curr_block)
					curr_block = {'from': None, 'to': None, 'sent': None, 'subject': None,
					              'type': 'reply', 'raw_header': [line_prediction['text']], 'text': []}
					mode = 2
					# nothing else to expect from this line, carry on!
					# note: there are cases where newlines are missing, ...
					continue

				# forward header in one line
				# ---------------------- Forwarded by Sherri Sera/Corp/Enron on 04/20/2001 12:21 PM --------------------
				if mode == 1 and re.match(r"-+ ?forward.+?-+", line_low):
					curr_block['raw_header'].append(line_prediction['text'])

					grps = re.search(r"-+ Forward(?:ed)? by (.+?) on (.+?)-+", line_prediction['text'],
					                 flags=re.IGNORECASE)
					# FIXME: this is not save to use, exceptions expected!
					curr_block['from'] = grps.group(1)
					curr_block['sent'] = grps.group(2)

					# take info from previous block
					curr_block['to'] = blocks[-1]['to']
					curr_block['subject'] = blocks[-1]['subject']

					curr_block = {'from': None, 'to': None, 'cc': None, 'sent': None, 'subject': None,
					              'type': None, 'raw_header': [], 'text': []}

					# next up: zombie mode (eat bodies)
					mode = 0

					# nothing else to expect from this line, carry on as zombie!
					continue

				# forward header in two lines
				# ---------------------- Forwarded by Charlotte Hawkins/HOU/ECT on 04/04/2000
				# 01:37 PM ---------------------------
				# TODO: are there more messed up cases?
				if mode == 1:
					curr_block['raw_header'].append(line_prediction['text'])

					try:
						# try eating the first line
						grps = re.search(r"-+ Forward(?:ed)? by (.+)", line_prediction['text'], flags=re.IGNORECASE)
						curr_block['to'] = blocks[-1]['to']
						grps = grps.group(1).split(' on ')
						curr_block['from'] = grps[0]
						# sometimes part of the date is already here...
						if len(grps) > 1:
							curr_block['sent'] = grps[1]
					except AttributeError:
						# must then be the second line?
						grps = re.search(r"(?:on )?(.+?)-+", line_prediction['text'], flags=re.IGNORECASE)
						# FIXME: this is not save to use, exceptions expected!
						curr_block['sent'] = ('' if curr_block['sent'] is None else curr_block[
							'sent']) + grps.group(1)
						mode = 0
					continue

				# eating a header and stumbled upon next one...
				if mode >= 2 and ('-- original' in line_low or '-- forward' in line_low):
					# TODO implement
					pass

				# TODO check if all fields are filled, potentially switch to new header
				# but how to distinguish new header from previous one? could just be a long list of recipients...

				# ended up here, so it's a normal reply header
				# TODO: figure out what to do with headers missing newlines
				# TODO: keep track of what you are eating (from, to, cc, ...) and append!
				# TODO: how to deal with multi-language?
				# TODO: how to deal with broken layouts?
				curr_block['raw_header'].append(line_prediction['text'])

				# On Tue, Jan 17, 2017 at 8:14 PM, Deepak Sharma <deepakmca05@gmail.com>
				# wrote:

				# > On Jan 18, 2017 9:39 AM, "Rishabh Bhardwaj" <rbnext29@gmail.com> wrote:

				# On Fri, Mar 24, 2017 at 3:52 PM, Kadam, Gangadhar (GE Aviation, Non-GE) <
				# Gangadhar.Kadam@ge.com> wrote:
				on_match = re.search(
					r"on (?:[a-z]+, ?)?([a-z]+ \d\d?, ?\d{2,4} (?:at )?\d\d?:\d\d ?(?:am|pm)),(.+?)(?:wrote|$)",
					line_prediction['text'], flags=re.IGNORECASE)
				if on_match:
					curr_block['sent'] = on_match.group(1)
					curr_block['type'] = 'unknown'  # this kind of header exists in both cases (or does it?)
					curr_block['from'] = on_match.group(2)
					curr_block['to'] = blocks[-1]['from']
					curr_block['subject'] = blocks[-1]['subject']
					mode = 3
					continue

				# attempt eating a from line (easy catch)
				# From: Charlotte Hawkins 03/30/2000 11:33 AM
				# From:	Michael Brown/ENRON@enronXgate on 04/19/2001 05:54 PM
				line_text = line_prediction['text']
				if 'from:' in line_low:
					mode = 3
					line_text = line_text.replace('From:', '').replace('from:', '')
				elif 'to:' in line_low and 'mailto:' not in line_low:
					mode = 4
					line_text = line_text.replace('To:', '').replace('to:', '')
				elif 'cc:' in line_low:
					mode = 5
					line_text = line_text.replace('Cc:', '').replace('cc:', '')
				elif 'sent:' in line_low or 'date:' in line_low:
					mode = 6
					line_text = line_text.replace('Sent:', '').replace('sent:', '')
				elif 'subject:' in line_low:
					mode = 7
					line_text = line_text.replace('Subject:', '').replace('subject:', '')

				if mode != 6:
					# time/date info often mixed with other stuff, so try to extract it from line
					# date pattern
					# '05/30/2001', 'May 29, 2001'
					date_match = re.search(r"((?:[a-z]+ \d{1,2}, ?\d{2,4})|(?:\d{1,2}/\d{1,2}/\d{2,4}))", line_low)
					if date_match:
						curr_block['sent'] = ('' if curr_block['sent'] is None else curr_block[
							'sent']) + ' ' + date_match.group(1)

					# time pattern
					# '09:43:45 AM',  '7:58 AM', '04:56 PM',
					time_match = re.search(r"(\d{1,2}:\d\d(?::\d\d)?(?: ?(?:pm|am))?)", line_low)
					if time_match:
						curr_block['sent'] = ('' if curr_block['sent'] is None else curr_block[
							'sent']) + ' ' + time_match.group(1)

				if mode > 2:
					field = ['', '', '', 'from', 'to', 'cc', 'sent', 'subject'][mode]
					curr_block[field] = ('' if curr_block[field] is None else curr_block[field]) + ' ' + line_text
					continue

				# last resort: might just be a leading from field with no prefix
				curr_block['from'] = ('' if curr_block['from'] is None else curr_block['from']) + ' ' + line_text

			# Sara Shackleton
			# 03/01/2000 07:43 AM
			# To: Mark Taylor/HOU/ECT@ECT
			# cc: Kaye Ellis/HOU/ECT@ECT
			# Subject: Trip to Brazil

			# Shirley Crenshaw
			# 09/06/2000 12:56 PM
			# To: ludkam@aol.com
			# cc:  (bcc: Vince J Kaminski/HOU/ECT)
			# Subject: Vince's Travel Itinerary

			#  -----Original Message-----
			# From: 	Crews, David
			# Sent:	Wednesday, May 30, 2001 10:11 AM
			# To:	Buy, Rick
			# Cc:	Gorte, David
			# Subject:	RE: FYI - Project Raven

			# 	Rick Buy/ENRON@enronXgate 05/30/01 09:20 AM 	   To: David Crews/Enron Communications@Enron Communications  cc: David Gorte/ENRON@enronXgate  Subject: RE: FYI - Project Raven

			#     -----Original Message-----
			#    From:   jennifer.d.sanders@us.andersen.com@ENRON
			#
			# [mailto:IMCEANOTES-jennifer+2Ed+2Esanders+40us+2Eandersen+2Ecom+40ENRON@ENRON.com]
			#
			#
			#
			#    Sent:   Tuesday, August 07, 2001 10:58 AM
			#    To:     Nemec, Gerald
			#    Subject:  Re: Hello!

			# To:   IMCEANOTES-jennifer+2Esanders/40us/2Eandersen/2Ecom/40ENRON@enron.com
			# cc:     (bcc: Jennifer D. Sanders)
			# Date: 08/07/2001 03:09 PM
			# From: Gerald.Nemec@enron.com
			# Subject:  RE: Hello!

			else:  # line_prediction != 'header'
				mode = 0
				curr_block['text'].append(line_prediction['text'])
		# todo only add block if it changed

		# end for line_prediction in email_predicted:
		blocks.append(curr_block)
		self._add_header_info(blocks, email_input)

		email_parsed = {
			'blocks': blocks}

		return email_parsed

# # join lines to blocks
# blocks = []
# prev = tp(pred[0]['predictions'])
# accu = []
# for l in pred:
#     ltp = tp(l['predictions'])
#     if prev != ltp:
#         blocks.append({
#             'type': prev,
#             'lines': accu
#         })
#         accu = []
#     prev = ltp
#     accu.append(l['text'])
# # add dangling accumulator
# blocks.append({
#     'type': prev,
#     'lines': accu
# })
#
# # parse header blocks
# for i, b in enumerate(blocks):
#     # don't care about non-headers
#     if b['type'] != 'Header':
#         continue
#
#     tmphead = {}
#     #for l in b['lines']:
#
#     # catch on:
#     # ---------------------- Forwarded by Charlotte Hawkins/HOU/ECT on 04/04/2000
#     # 01:37 PM ---------------------------
#     # or
#     # ---------------------- Forwarded by Sherri Sera/Corp/Enron on 04/20/2001 12:21 PM --------------------------
#     # but don't confuse with
#     # -----Original Message-----
#     #for l in b['lines']:
#         #if 'forward' in l.lower():
