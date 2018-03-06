import re
import sre_constants
from collections import Counter

# implements features described in
# A. Lampert, R. Dale, C. Paris. Segmenting Email Message Text into Zones. In: Proceedings of EMNLP 2009
# there is also a Scala impelementation: https://github.com/gerhardgossen/soZebra

# from scikit learn https://github.com/scikit-learn/scikit-learn/blob/ef5cb84a/sklearn/feature_extraction/text.py#L456
token_pattern = re.compile(r"(?u)\b\w\w+\b")  # then .findall(str)


def tokenise(s, ngrams=1):
    tok = token_pattern.findall(s)
    ret = []
    for i, _ in enumerate(tok):
        if (i + ngrams) <= len(tok):
            ret.append(' '.join(tok[i:i + ngrams]))
    return ret


def mail2fragments(maill):
    """
    find boundaries (see section 4.1.2 of paper)
    
    :param maill: mail as list of str (lines) 
    :return: list of lists (fragments[lines])
    """
    fragments = []
    tmp_fragment = []
    for i, line in enumerate(maill):
        if re.search(r"^\s*([!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]{4,}|$)", line):
            if len(tmp_fragment) > 0:
                fragments.append(tmp_fragment)
                tmp_fragment = []
        tmp_fragment.append(line)
    fragments.append(tmp_fragment)


def contains_name(name, fragment):
    """
    tests if fragment contains a given name
    :param name: sender's or recipient's name
    :param fragment: haystack
    :return: bool
    """
    # TODO implement
    return True


def percentage(num, total):
    if total > 0:
        return num / total
    return 0.0


def names2regex(names):
    if type(names) == list:
        names = ' '.join(names)
    return '(?:' + ('|'.join(re.split(r"(?:\s+[,;]?\s*|\s*[,;]?\s+)", names))) + ')'


def mail2features(m):
    mail = m.body
    maill = m.lines
    clean_lines = m.lines_clean

    unigrams = tokenise(mail, 1)
    bigrams = tokenise(mail, 2)
    c_unigrams = Counter(unigrams)
    c_bigrams = Counter(bigrams)

    subject_reply_marker = re.search(r"^\s*re:", m.subject, flags=re.IGNORECASE)
    subject_forward_marker = re.search(r"^\s*fw:", m.subject, flags=re.IGNORECASE)

    mail_features = []
    for i, line in enumerate(maill):
        features = {}
        tokenised = tokenise(line, 1)

        # == GRAPHIC FEATURES (section 4.3.1) ==

        # the number of words in the text fragment
        features['num_words'] = len(tokenised)

        # the number of unicode code points (i.e. characters) in the text fragment
        # [same as num chars??]
        # the average line length (in chars) within the text fragment (line len for line-based)
        features['num_chars'] = len(line)

        # the start position of the text fragment (first line of message = 1)
        features['line_num_start'] = i + 1
        # the start position of the text fragment (first line = 1, normalised by message len)
        features['line_num_start_rel'] = (i + 1) / (len(maill) + 1)

        # the end position of the text fragment
        features['line_num_end'] = i + 2
        # and again normalised for message length
        features['line_num_end_rel'] = (i + 2) / (len(maill) + 1)

        # the length of the text fragment (in chars) relative to previous fragment
        features['len_rel_to_prev'] = len(line) - len(maill[i - 1]) if i > 0 else 0
        # the length of the text fragment (in chars) relative to next fragment
        features['len_rel_to_prev'] = len(line) - len(maill[i + 1]) if (i + 1) < len(maill) else 0

        # the number of blank lines preceding the text fragment
        cnt = 0
        for j in reversed(range(0, i)):
            if re.search(r"^\s*$", maill[j]):
                cnt += 1
            else:
                break
        features['blank_lines_prev'] = cnt

        # the number of blank lines following the text fragment
        cnt = 0
        for j in range(i + 1, len(maill)):
            if re.search(r"^\s*$", maill[j]):
                cnt += 1
            else:
                break
        features['blank_lines_next'] = cnt

        # == ORTHOGRAPHIC FEATURES  (section 4.3.2) ==

        # whether all lines start with the same character (e.g. '>')
        if re.search(r"^\s*[!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]{2,}", line):
            features['repeated_punct_begin'] = 1

        # whether a prior text fragment in the message contains a quoted header
        if i > 0 and re.search(r"^\s*(?:from|to|sent|cc|bcc|date|subject):", maill[i - 1], flags=re.IGNORECASE):
            features['contains_quoted_header_prev'] = 1

        # whether a prior text fragment in the message contains repeated punctuation characters
        if i > 0 and re.search(r"[!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]{2,}", maill[i - 1]):
            features['repeated_punct_prev'] = 1

        # whether the text fragment contains a URL
        if re.search(r"(?:https?://)?(www3?\.)?[a-z0-9.-]+\.(?:de|com|org|net|co\.uk)", line, flags=re.IGNORECASE):
            features['contains_url'] = 1

        # whether the text fragment contains an email address
        if re.search(r".*[\w\d]+@[\w\d+]{2,}.*", line):
            features['contains_email'] = 1

        # whether the text fragment contains a sequence of four or more digits
        if re.search(r"\d{4,}", line):
            features['contains_digit_sequence'] = 1

        num_cap_words = len(list(filter(lambda t: t[0].istitle(), tokenised)))
        # the number of capitalised words in the text fragment
        features['num_uppercase_words'] = num_cap_words
        # the percentage of capitalised words in the text fragment
        features['perc_uppercase_words'] = percentage(num_cap_words, len(line))

        num_non_alpha = len(re.findall(r"[^A-Za-z0-9 ]", line))
        # the number of non-alpha-numeric characters in the text fragment
        features['num_non_alphanumeric_chars'] = num_non_alpha
        # the percentage of non-alpha-numeric characters in the text fragment
        features['perc_non_alphanumeric_chars'] = percentage(num_non_alpha, len(line))

        num_numeric_chars = len(re.findall(r"\d", line))
        # the number of numeric characters in the text fragment
        features['num_numeric_chars'] = num_numeric_chars
        # the percentage of numeric characters in the text fragment
        features['perc_numeric_chars'] = percentage(num_numeric_chars, len(line))

        # whether the message subject line contains a reply syntax marker such as Re:
        if subject_reply_marker:
            features['subject_reply_marker'] = 1

        # whether te message subject line contains a forward syntax marker such as Fw:
        if subject_forward_marker:
            features['subject_forward_marker'] = 1

        # == LEXICAL FEATURES (section 4.3.3) ==

        # each word unigram, calculated with a min freq threshold of 3, represented as a separate bin feature
        for t in tokenised:
            if c_unigrams[t] > 3:
                features['unigram=' + t] = 1

        # each word bigram, calculated with a min freq threshold of 3, represented as a separate bin feature
        for t in tokenise(line, 2):
            if c_bigrams[t] > 3:
                features['bigram=' + t.replace(' ', '_')] = 1

        # whether the text fragment contains the sender's name
        if re.search(names2regex(m.xsender), line):
            features['contains_senders_name'] = 1

        # whether a prior text fragment contains the sender's name
        if re.search(names2regex(m.xsender), line):
            features['contains_senders_name_prev'] = 1

        # whether the text fragment contains the sender's initials
        try:
            initials = [re.sub(r"\|\(\)\+\^\$\*", '', p[0]) for p in re.split(r"(?:\s+[,;]?\s*|\s*[,;]?\s+)", m.xsender)][
                       0:2]
            initials_regex = "(?:" + (''.join(initials)) + '|' + ('.'.join(initials) + '.') + '|' + \
                             ('. '.join(initials) + '.')
            if len(initials) > 1:
                initials = [initials[0]] + [initials[-1]]
                initials_regex += '|' + (''.join(initials)) + '|' + ('.'.join(initials) + '.') + '|' + \
                                  ('. '.join(initials) + '.')
            initials_regex += ')'
            if re.search(initials_regex, line):
                features['contains_senders_initials'] = 1
        except IndexError:
            pass

        # whether the text fragment contains a recipient's name
        try:
            if re.search(names2regex(m.xto), line):
                features['contains_recipients_name'] = 1
        except sre_constants.error:
            pass

        mail_features.append(features)

    return mail_features
