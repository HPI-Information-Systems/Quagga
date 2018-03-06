import re


def clean_line(s):
    s = s.replace('=\n', '').replace('=20', '').replace('=09', '').replace('=01\&', '') \
        .replace('=01&', '').replace('=18', '').replace('=018', '')

    # remove attachments
    s = re.sub(r"\s*\[IMAGE\]\s*", "", s, flags=re.I)
    s = re.sub(r"<<.{3,50}\.(xls|xlsx|png|gif|jpg|jpeg|doc|docx|ppt|pptx|pst)>>%?", "", s, flags=re.I)
    s = re.sub(r"^\s*-.{3,50}\.(xls|xlsx|png|gif|jpg|jpeg|doc|docx|ppt|pptx|pst)%?", "", s, flags=re.I)

    return s


def parse_xfrom(xfrom):
    fn = None
    ln = None
    mail = None

    match = re.search(r"(?P<ln>\w+), (?P<fn>\w+)(?: ?(?P<mn>\w)\.?)?", xfrom)
    if match:
        fn = match.group('fn')
        ln = match.group('ln')
    else:
        match = re.search(r"(?P<fn>\w+) (?:(?P<mn>\w)\.? )?(?P<ln>\w+)", xfrom)
        if match:
            fn = match.group('fn')
            ln = match.group('ln')
        else:
            fn = re.sub(r"\W", "", xfrom.split(' ')[0], flags=re.I)

    match = re.search(r"(?P<mail>[a-z0-9.\-_]+@[a-z0-9.\-_]+\.[a-z]{2,3})", xfrom, flags=re.I)
    if match:
        mail = match.group('mail')

    return fn, ln, mail


PUNCTUATION = re.compile(r"[!\"#$%&\')(*+,-./:;<=>?@\]\[^_´}{~]")


def mail2features(mail):
    lines = mail.lines
    mail_features = []
    num_lines = len(lines)
    fn, ln, ml = parse_xfrom(mail.xsender)

    for li, line in enumerate(lines):
        cline = clean_line(line)
        len_line = len(line)
        line_lower = line.lower()

        features = {}

        features['blank_line:0'] = len(cline.strip()) == 0
        features['emailpattern:0'] = bool(re.search(r"[a-z0-9.\-_]+@[a-z0-9.\-_]+\.[a-z]{2,3}", line, flags=re.I))
        features['lastline:0'] = (num_lines - 1) == li
        features['prevToLastLine:0'] = (num_lines - 2) == li
        # email header pattern
        # url pattern
        # phone number pattern
        features['containsPhonePattern:0'] = bool(re.search(r"(?:\(\d+\) ?)\d+(?: ?- ?\d+)?", line))
        features['signatureMarker:0'] = bool(re.search(r"-{3,}", line))
        features['signatureMarker2:0'] = bool(re.search(r"_{3,}", line))
        features['signatureMarker3:0'] = bool(re.search(r"\*{3,}", line))
        features['5special:0'] = bool(re.search(r"^\s*(\*|#|\+|\^|-|~|_|&|/|\$|!|%|:|=){5,}", line))

        # typical signature words (dept, university, corp,...)
        features['namePattern:0'] = bool(re.search(r"[A-Z][a-z]+\s\s?[A-Z]\.?\s\s?[A-Z][a-z]+", line))
        features['quoteEnd:0'] = bool(re.search(r"\"$", line))
        features['containsSenderName_first:0'] = bool(fn) and fn.lower() in line_lower
        features['containsSenderName_last:0'] = bool(ln) and ln.lower() in line_lower
        features['containsSenderName_mail:0'] = bool(ml) and ml.lower() in line_lower

        n_tabs = line.count('\t')
        features['numTabs=1:0'] = n_tabs == 1
        features['numTabs=2:0'] = n_tabs == 2
        features['numTabs>=3:0'] = n_tabs >= 3

        n_words = len(re.findall(r"\w+", line))
        features['numWords=1'] = n_words == 1
        features['numWords=2'] = n_words == 2
        features['numWords<=5'] = 2 < n_words <= 5
        features['numWords>5'] = n_words > 5

        puncts = len(PUNCTUATION.findall(line))
        features['punctuation>20:0'] = len_line > 0 and puncts / len_line > 0.2
        features['punctuation>50:0'] = len_line > 0 and puncts / len_line > 0.5
        features['punctuation>90:0'] = len_line > 0 and puncts / len_line > 0.9
        features['typicalMarker:0'] = bool(re.search(r"^>", line))
        features['startWithPunct:0'] = bool(PUNCTUATION.match(line))
        features['nextSamePunct:0'] = True if (li + 1 >= num_lines or 0 == len_line == len(lines[li + 1])) else \
            (bool(PUNCTUATION.match(lines[li + 1])) and len_line > 0 and
             len(lines[li + 1]) > 0 and lines[li + 1][0] == line[0])
        features['prevSamePunct:0'] = True if (li - 1 >= 0 or 0 == len_line == len(lines[li - 1])) else \
            (bool(PUNCTUATION.match(lines[li - 1])) and len_line > 0 and
             len(lines[li - 1]) > 0 and lines[li - 1][0] == line[0])

        # starts with 1-2 punct followed by reply marker: "^\p{Punct}{1,2}\>"
        # reply line clue: "wrote:$" or "writes:$"
        alphnum = len(re.findall('[a-zA-Z0-9]', line))
        features['alphnum<90:0'] = len_line > 0 and (alphnum / len_line) < 0.9
        features['alphnum<50:0'] = len_line > 0 and (alphnum / len_line) < 0.5
        features['alphnum<10:0'] = len_line > 0 and (alphnum / len_line) < 0.1
        features['hasWord=fwdby:0'] = bool(re.search(r"forwarded by", line, flags=re.I))
        features['hasWord=origmsg:0'] = bool(re.search(r"original message", line, flags=re.I))
        features['hasWord=fwdmsg:0'] = bool(re.search(r"forwarded message", line, flags=re.I))
        features['hasWord=from:0'] = bool(re.search(r"from:", cline, flags=re.I))
        features['hasWord=to:0'] = bool(re.search(r"to:", cline, flags=re.I))
        features['hasWord=subject:0'] = bool(re.search(r"subject:", cline, flags=re.I))
        features['hasWord=cc:0'] = bool(re.search(r"cc:", cline, flags=re.I))
        features['hasWord=bcc:0'] = bool(re.search(r"bcc:", cline, flags=re.I))
        features['hasWord=subj:0'] = bool(re.search(r"subj:", cline, flags=re.I))
        features['hasWord=date:0'] = bool(re.search(r"date:", cline, flags=re.I))
        features['hasWord=sent:0'] = bool(re.search(r"sent:", cline, flags=re.I))
        features['hasWord=sentby:0'] = bool(re.search(r"sent by:", cline, flags=re.I))
        features['hasWord=fax:0'] = bool(re.search(r"fax", cline, flags=re.I))
        features['hasWord=phone:0'] = bool(re.search(r"phone", cline, flags=re.I))
        features['hasWord=cell:0'] = bool(re.search(r"cell", cline, flags=re.I))
        features['beginswithShape=Xx{2,8}\::0'] = bool(re.search(r"[A-Z][a-z]{1,7}:", cline))
        features['hasForm=^dd/dd/dddd dd:dd ww$:0'] = \
            bool(re.search(r"^\s*\d\d/\d\d/\d\d\d\d \d?\d:\d\d(?::\d\d)? ?(?:am|pm)?\s*$", cline, flags=re.I))
        features['hasForm=^dd:dd:dd ww$:0'] = \
            bool(re.search(r"^\s*\d\d:\d\d(?::\d\d)? ?(?:am|pm)\s*$", cline, flags=re.I))
        features['containsForm=dd/dd/dddd dd:dd ww:0'] = \
            bool(re.search(r"on\s*\d\d/\d\d/\d\d\d\d \d?\d:\d\d(?::\d\d)? ?(?:am|pm)?", cline, flags=re.I))
        features['hasLDAPthings'] = bool(re.search(r"\w+ \w+/[A-Z]{1,4}/[A-Z]{2,8}@[A-Z]{2,8}", cline))

        features['endsWith=,'] = bool(re.search(r",\s*$", line))
        features['endsWith=!'] = bool(re.search(r"!\s*$", line))
        features['endsWith=:'] = bool(re.search(r":\s*$", line))

        features['startsWith=hi'] = bool(re.search(r"^\s*>?\s*hi", line, flags=re.IGNORECASE))
        features['startsWith=dear'] = bool(re.search(r"^\s*>?\s*dear", line, flags=re.IGNORECASE))
        features['startsWith=hey'] = bool(re.search(r"^\s*>?\s*hey", line, flags=re.IGNORECASE))
        features['startsWith=facsimile'] = bool(re.search(r"^\s*>?\s*facsimile:", line, flags=re.IGNORECASE))
        features['startsWith=fax'] = bool(re.search(r"^\s*>?\s*fax:", line, flags=re.IGNORECASE))
        features['startsWith=phone'] = bool(re.search(r"^\s*>?\s*phone:", line, flags=re.IGNORECASE))
        features['startsWith=mail'] = bool(re.search(r"^\s*>?\s*e?-?mail\s*(?:address)?\s*:", line, flags=re.IGNORECASE))
        features['startsWith=cell'] = bool(re.search(r"^\s*>?\s*cell:", line, flags=re.IGNORECASE))
        features['startsWith=home'] = bool(re.search(r"^\s*>?\s*home:", line, flags=re.IGNORECASE))

        features['containsSenderName_any:0'] = features['containsSenderName_first:0'] or \
                                               features['containsSenderName_last:0'] or \
                                               features['containsSenderName_mail:0']

        features['containsMimeWord:0'] = features['hasWord=from:0'] or \
                                         features['hasWord=to:0'] or \
                                         features['hasWord=cc:0'] or \
                                         features['hasWord=bcc:0'] or \
                                         features['hasWord=subject:0'] or \
                                         features['hasWord=subj:0'] or \
                                         features['hasWord=date:0'] or \
                                         features['hasWord=sent:0'] or \
                                         features['hasWord=sentby:0']

        features['containsHeaderStart:0'] = features['hasWord=fwdby:0'] or \
                                            features['hasWord=origmsg:0'] or \
                                            features['hasWord=fwdmsg:0']

        features['containsSignatureWord:0'] = features['hasWord=fax:0'] or \
                                              features['hasWord=cell:0'] or \
                                              features['hasWord=phone:0']

        for k, v in features.items():
            if type(v) == bool:
                features[k] = 1 if v else -1
        # print(list(features.keys()))
        mail_features.append(features)

    return mail_features
