import re

"""Module for generating a feature representation of each line in an email

This code is a Python translation of the original Jangada source code 
(see scripts/Jangada/original/src/jangada/SigFilePredictor.java)
Structure and variable names are more or less kept for easier code comparison
"""

# constants
tail_lines = 10


def detect_from_name(input_str, test_line):
    pattern1 = "([A-Z][a-z]+\s\s?[A-Z]?\.?\s\s?([A-Z][a-z]+))"
    pattern2 = "([A-Z][a-z]+\s\s?([A-Z][a-z]+))"

    # Compile and use regular expressions
    match1 = re.search(pattern1, input_str)
    match2 = re.search(pattern2, input_str)

    # try first pattern name first (Vitor R. Carvalho)
    if match1 is not None:
        for match in match1.groups():
            if match in test_line:
                return True
    # try another string pattern (Vitor Carvalho)
    elif match2 is not None:
        for match in match2.groups():
            if match in test_line:
                return True

    # in case nothing was found
    return False


def start_with_same_initial_punct_characters(line1, line2):
    if len(line1) > 0 and len(line2) > 0:
        char1 = line1[0]
        char2 = line2[0]
        if char1 in "!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~":
            return char1 == char2
    return False


def indent_number(line):
    if len(line) == 0:
        return 0
    return len([c for c in line if c == "\t"])


def indent_percentage(line):
    num = indent_number(line)
    if num == 0:
        return 0.0
    return num / len(line)


def punctuation_number(line):
    return len([c for c in line if c in "!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"])


def punctuation_percentage(line):
    num = punctuation_number(line)
    if len(line) == 0:
        return 0.0
    return num / len(line)


def word_character_number(line):
    return len([c for c in line if re.match("\w", c)])


def word_character_percentage(line):
    num = word_character_number(line)
    if len(line) == 0:
        return 0.0
    return num / len(line)


def mail2features(mail):
    mail = mail.lines
    # findFromLine(s)
    from_lines = []
    for i, line in enumerate(mail):
        if re.search("^\s*[!\"#$%&'()*+,-./:;<=>?@\[\]^_`{|}~]?\s*[F|f][R|r][O|o][M|m]:", line):
            from_lines.append(i)

    size = len(mail)
    mail_features = []
    for i, line in enumerate(mail):
        features = {}

        # check first line features
        if i == 0:
            features['firstL'] = 1
        if i == 1:
            features['secondL'] = 1

        # check last line feature
        if i == size - 1:
            features['lastL'] = 1
        if i == size - 2:
            features['lastbutoneL'] = 1
        if i == size - 3:
            features['lastbutbutoneL'] = 1

        # header feature
        if re.search("^\s?\s?(?:\w|-)+:", line):
            if re.search("^\s?\s?(?:http|HTTP|Phone|PHONE|phone|email|EMAIL|Internet|INTERNET|internet)+:", line):
                features['header'] = 1
            if (size - i) < tail_lines:
                features['closeheader'] = 1

        # blank line features
        regex_blank_line = r"^\s*$"
        if i > 1:
            if re.search(regex_blank_line, mail[i - 2]):
                features['prevprevblankL'] = 1
                if (size - i) < (tail_lines + 2):
                    features['closeprevprevblankL'] = 1
        if i > 0:
            if re.search(regex_blank_line, mail[i - 1]):
                features['prevblankL'] = 1
                if (size - i) < (tail_lines + 1):
                    features['closeprevblankL'] = 1
        if re.search(regex_blank_line, mail[i]):
            features['blankL'] = 1
            if (size - i) < tail_lines:
                features['closeblankL'] = 1
        else:
            features['notblankL'] = 1
        if i < (size - 1):
            if re.search(regex_blank_line, mail[i + 1]):
                features['nextblankL'] = 1
                if (size - i) < tail_lines:
                    features['closenextblanL'] = 1
        if i < (size - 2):
            if re.search(regex_blank_line, mail[i + 2]):
                features['nextnextblankL'] = 1
                if (size - i) < tail_lines:
                    features['closenextnextblanL'] = 1

        # sig marker feature
        regex_sig_marker = r"^\s*---*\s*$"
        if i > 0:
            if re.search(regex_sig_marker, mail[i - 1]):
                features['prevsigMarker'] = 1
                if (size - i) < tail_lines:
                    features['closeprevsigMarker'] = 1
        if re.search(regex_sig_marker, mail[i]):
            features['sigMarker'] = 1
            if (size - i) < tail_lines:
                features['closesigMarker'] = 1
        if i < (size - 1):
            if re.search(regex_sig_marker, mail[i + 1]):
                features['nextsigMarker'] = 1
                if (size - i) < tail_lines:
                    features['closenextsigMarker'] = 1

        # trueSigMarker - post-addition
        regex_true_sig_marker = r"^\s?\s?---?\s*$"
        if i > 3:
            if re.search(regex_true_sig_marker, mail[i - 4]):
                features['prevprevprevprevtruesigMarker'] = 1
                if (size - i) < (tail_lines + 4):
                    features['prevprevprevprevclosetruesigMarker'] = 1
        if i > 2:
            if re.search(regex_true_sig_marker, mail[i - 3]):
                features['prevprevprevtruesigMarker'] = 1
                if (size - i) < (tail_lines + 3):
                    features['prevprevprevclosetruesigMarker'] = 1
        if i > 1:
            if re.search(regex_true_sig_marker, mail[i - 2]):
                features['prevprevtruesigMarker'] = 1
                if (size - i) < (tail_lines + 2):
                    features['prevprevclosetruesigMarker'] = 1
        if i > 0:
            if re.search(regex_true_sig_marker, mail[i - 1]):
                features['prevtruesigMarker'] = 1
                if (size - i) < (tail_lines + 1):
                    features['prevclosetruesigMarker'] = 1
        if re.search(regex_true_sig_marker, mail[i]):
            features['truesigMarker'] = 1
            if (size - i) < tail_lines:
                features['closetruesigMarker'] = 1
        if i < (size - 1):
            if re.search(regex_true_sig_marker, mail[i + 1]):
                features['nexttruesigMarker'] = 1
                if (size - i) < tail_lines:
                    features['nextclosetruesigMarker'] = 1
        if i < (size - 2):
            if re.search(regex_true_sig_marker, mail[i + 2]):
                features['nextnexttruesigMarker'] = 1
                if (size - i) < tail_lines:
                    features['nextnextclosetruesigMarker'] = 1
        if i < (size - 3):
            if re.search(regex_true_sig_marker, mail[i + 3]):
                features['nextnextnexttruesigMarker'] = 1
                if (size - i) < tail_lines:
                    features['nextnextnextclosetruesigMarker'] = 1

        # other markers features
        regex_other_markers = r"^\s*(?:\*|#|\+|\^|-|~|&|/|\$|_|!|/|%|:|=){10,}\s*$"
        if i > 0:
            if re.search(regex_other_markers, mail[i - 1]):
                features['prevotherMarkers'] = 1
                if (size - i) < tail_lines:
                    features['closeprevotherMarkers'] = 1
        if re.search(regex_other_markers, mail[i]):
            features['otherMarkers'] = 1
            if (size - i) < tail_lines:
                features['closeotherMarkers'] = 1
        if i < (size - 1):
            if re.search(regex_other_markers, mail[i + 1]):
                features['nextotherMarkers'] = 1
                if (size - i) < tail_lines:
                    features['closenextotherMarkers'] = 1

        # special works feature
        regex_special_works = r"Dept\.|University|Corp\.|Corporations?|College|Ave\.|Laboratory|[D|d]isclaimer|Division|Professor|Laboratories|Institutes?|Services|Engineering|Director|Sciences?|Address|Fax|Office|Mobile|Phone|Manager|Street|St\.|Avenue"
        if i > 0:
            if re.search(regex_special_works, mail[i - 1]):
                features['prevspecWords'] = 1
                if (size - i) < tail_lines:
                    features['closeprevspecWords'] = 1
        if re.search(regex_special_works, mail[i]):
            features['specWords'] = 1
            if (size - i) < tail_lines:
                features['closespecWords'] = 1
        if i < (size - 1):
            if re.search(regex_special_works, mail[i + 1]):
                features['nextspecWords'] = 1
                if (size - i) < tail_lines:
                    features['closenextspecWords'] = 1

        # email feature
        regex_email = r"(?:\w|\+|\.|-)+@(?:\w|\+|\.|-)+\.[a-zA-z]{2,5}"
        if i > 0:
            if re.search(regex_email, mail[i - 1]):
                features['prevemail'] = 1
                if (size - i) < tail_lines:
                    features['closeprevemail'] = 1
        if re.search(regex_email, mail[i]):
            features['email'] = 1
            if (size - i) < tail_lines:
                features['closeemail'] = 1
        if i < (size - 1):
            if re.search(regex_email, mail[i + 1]):
                features['nextemail'] = 1
                if (size - i) < tail_lines:
                    features['closenextemail'] = 1
        if re.search(r"[^<>](?:\w|\+|-)+@(?:\w|-)+\.[a-zA-z]{2,5}", mail[i]):
            features['emailB'] = 1
            if (size - i) < tail_lines:
                features['closeemailB'] = 1

        # URL feature
        regex_url = r"\s?(?:http://)*(?:www|web|w3)*\w(?:\w|-)+\.\w(?:\w|-)+\.\w(?:\w|-)*\w+"
        if i > 0:
            if re.search(regex_url, mail[i - 1]):
                features['preveurl'] = 1
                if (size - i) < tail_lines:
                    features['closeprevurl'] = 1
        if re.search(regex_url, mail[i]):
            features['url'] = 1
            if (size - i) < tail_lines:
                features['closeurl'] = 1
        if i < (size - 1):
            if re.search(regex_url, mail[i + 1]):
                features['nexturl'] = 1
                if (size - i) < tail_lines:
                    features['closenexturl'] = 1

        # phone
        regex_phone = r"(?:-?\d)*\d\d\s?-?\s?\d\d\d\d"
        if i > 0:
            if re.search(regex_phone, mail[i - 1]):
                features['prevephone'] = 1
        if re.search(regex_phone, mail[i]):
            features['phone'] = 1
        if i < (size - 1):
            if re.search(regex_phone, mail[i + 1]):
                features['nextphone'] = 1

        # names like Vitor R.Carvalho or John F.Kennedy
        if re.search(r"[A-Z][a-z]+\s\s?[A-Z]\.?\s\s?[A-Z][a-z]+", mail[i]):
            features['namepat'] = 1
            if (size - i) < tail_lines:
                features['closenamepat'] = 1

        # end-of-line quotes
        if re.search("\"$", mail[i]):
            features['endQuote'] = 1
            if (size - i) < tail_lines:
                features['closeendQuote'] = 1

        # FROM line feature
        if len(from_lines) > 0:
            if detect_from_name(mail[from_lines[0]], mail[i]):
                features['fromL'] = 1
                if (size - i) < tail_lines:
                    features['closefromL'] = 1
            if i < (size - 1):
                if detect_from_name(mail[from_lines[0]], mail[i + 1]):
                    features['nextfromL'] = 1
                    if (size - i) < tail_lines:
                        features['closenextfromL'] = 1

        # reply symbol
        regex_reply_symbol = "^\s*>.*"
        if i > 0:
            if re.search(regex_reply_symbol, mail[i - 1]):
                features['prevreplySymbol'] = 1
        if re.search(regex_reply_symbol, mail[i]):
            features['replySymbol'] = 1
        if i < (size - 1):
            if re.search(regex_reply_symbol, mail[i + 1]):
                features['nextreplySymbol'] = 1

        # other reply symbol
        regex_other_reply_symbol = r"^(?:=|:|#|-|\+|&|%|\})\s*\w+.*"
        if i > 0:
            if re.search(regex_other_reply_symbol, mail[i - 1]):
                features['prevotherreplySymbol'] = 1
        if re.search(regex_other_reply_symbol, mail[i]):
            features['otherreplySymbol'] = 1
        if i < (size - 1):
            if re.search(regex_other_reply_symbol, mail[i + 1]):
                features['nextotherreplySymbol'] = 1

        # punct starting and followed by ">"
        regex_punct_gr = r"^[!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]{1,2}>.*"
        if i > 0:
            if re.search(regex_punct_gr, mail[i - 1]):
                features['prevpunct'] = 1
        if re.search(regex_punct_gr, mail[i]):
            features['punct'] = 1
        if i < (size - 1):
            if re.search(regex_punct_gr, mail[i + 1]):
                features['nextpunct'] = 1

        # writes and wrote features
        regex_writes = r" writes:\s*$"
        regex_wrote = r" wrote:\s*$"
        if i > 0:
            if re.search(regex_writes, mail[i - 1]):
                features['prevwrites'] = 1
            if re.search(regex_wrote, mail[i - 1]):
                features['prevwrote'] = 1
        if re.search(regex_writes, mail[i]):
            features['writes'] = 1
        if re.search(regex_wrote, mail[i]):
            features['wrote'] = 1
        if i < (size - 1):
            if re.search(regex_writes, mail[i + 1]):
                features['nextwrites'] = 1
            if re.search(regex_wrote, mail[i + 1]):
                features['nextwrote'] = 1

        # same initial punct characters
        if i > 0 and start_with_same_initial_punct_characters(mail[i], mail[i - 1]):
            features['prevsicline'] = 1
            if (size - i) < tail_lines:
                features['closeprevsicline'] = 1
        if i < (size - 1) and start_with_same_initial_punct_characters(mail[i], mail[i + 1]):
            features['nextsicline'] = 1
            if (size - i) < tail_lines:
                features['closenextsicline'] = 1

        # number of leading tabs
        ddd = indent_number(mail[i])
        if ddd == 1:
            features['indentUni'] = 1
            if (size - i) < tail_lines:
                features['closeindentUni'] = 1
        if ddd == 2:
            features['indentBi'] = 1
            if (size - i) < tail_lines:
                features['closeindentBi'] = 1
        if ddd == 3:
            features['indentTri'] = 1
            if (size - i) < tail_lines:
                features['closeindentTri'] = 1
        if i > 0:
            ddd = indent_number(mail[i - 1])
            if ddd == 1:
                features['previndentUni'] = 1
                if (size - i) < tail_lines:
                    features['closeprevindentUni'] = 1
            if ddd == 2:
                features['previndentBi'] = 1
                if (size - i) < tail_lines:
                    features['closeprevindentBi'] = 1
            if ddd == 3:
                features['previndentTri'] = 1
                if (size - i) < tail_lines:
                    features['closeprevindentTri'] = 1
        if i < (size - 1):
            ddd = indent_number(mail[i + 1])
            if ddd == 1:
                features['nextindentUni'] = 1
                if (size - i) < tail_lines:
                    features['closenextindentUni'] = 1
            if ddd == 2:
                features['nextindentBi'] = 1
                if (size - i) < tail_lines:
                    features['closenextindentBi'] = 1
            if ddd == 3:
                features['nextindentTri'] = 1
                if (size - i) < tail_lines:
                    features['closenextindentTri'] = 1

        # punctuation percentage
        temp = punctuation_percentage(mail[i])
        if temp > 0.2:
            features['punctPerc20'] = 1
            if (size - i) < tail_lines:
                features['closepunctPerc20'] = 1
        else:
            features['punctPerc0'] = 1
            if (size - i) < tail_lines:
                features['closepunctPerc0'] = 1
        if temp > 0.5:
            features['punctPerc50'] = 1
            if (size - i) < tail_lines:
                features['closepunctPerc50'] = 1
        if temp > 0.75:
            features['punctPerc75'] = 1
            if (size - i) < tail_lines:
                features['closepunctPerc75'] = 1
        if temp > 0.9:
            features['punctPerc90'] = 1
            if (size - i) < tail_lines:
                features['closepunctPerc90'] = 1
        if i > 0:
            temp = punctuation_percentage(mail[i - 1])
            if temp > 0.2:
                features['punctPerc20prev'] = 1
                if (size - i) < tail_lines:
                    features['closepunctPerc20prev'] = 1
            if temp > 0.5:
                features['punctPerc50prev'] = 1
                if (size - i) < tail_lines:
                    features['closepunctPerc50prev'] = 1
            if temp > 0.75:
                features['punctPerc75prev'] = 1
                if (size - i) < tail_lines:
                    features['closepunctPerc75prev'] = 1
            if temp > 0.9:
                features['punctPerc90prev'] = 1
                if (size - i) < tail_lines:
                    features['closepunctPerc90prev'] = 1
        if i < (size - 1):
            temp = punctuation_percentage(mail[i + 1])
            if temp > 0.2:
                features['punctPerc20next'] = 1
                if (size - i) < tail_lines:
                    features['closepunctPerc20next'] = 1
            if temp > 0.5:
                features['punctPerc50next'] = 1
                if (size - i) < tail_lines:
                    features['closepunctPerc50next'] = 1
            if temp > 0.75:
                features['punctPerc75next'] = 1
                if (size - i) < tail_lines:
                    features['closepunctPerc75next'] = 1
            if temp > 0.9:
                features['punctPerc90next'] = 1
                if (size - i) < tail_lines:
                    features['closepunctPerc90next'] = 1

        # word characters percentage
        temp = word_character_percentage(mail[i])
        if temp > 0.2:
            features['charPerc20'] = 1
            if (size - i) < tail_lines:
                features['closecharPerc20'] = 1
        else:
            features['charPerc0'] = 1
            if (size - i) < tail_lines:
                features['closecharPerc0'] = 1
        if temp > 0.5:
            features['charPerc50'] = 1
            if (size - i) < tail_lines:
                features['closecharPerc50'] = 1
        if temp > 0.75:
            features['charPerc75'] = 1
            if (size - i) < tail_lines:
                features['closecharPerc75'] = 1
        if temp > 0.9:
            features['charPerc90'] = 1
            if (size - i) < tail_lines:
                features['closecharPerc90'] = 1
        if i > 0:
            temp = word_character_percentage(mail[i - 1])
            if temp > 0.2:
                features['charPerc20prev'] = 1
                if (size - i) < tail_lines:
                    features['closecharPerc20prev'] = 1
            if temp > 0.5:
                features['charPerc50prev'] = 1
                if (size - i) < tail_lines:
                    features['closecharPerc50prev'] = 1
            if temp > 0.75:
                features['charPerc75prev'] = 1
                if (size - i) < tail_lines:
                    features['closecharPerc75prev'] = 1
            if temp > 0.9:
                features['charPerc90prev'] = 1
                if (size - i) < tail_lines:
                    features['closecharPerc90prev'] = 1
        if i < (size - 1):
            temp = word_character_percentage(mail[i + 1])
            if temp > 0.2:
                features['charPerc20next'] = 1
                if (size - i) < tail_lines:
                    features['closecharPerc20next'] = 1
            if temp > 0.5:
                features['charPerc50next'] = 1
                if (size - i) < tail_lines:
                    features['closecharPerc50next'] = 1
            if temp > 0.75:
                features['charPerc75next'] = 1
                if (size - i) < tail_lines:
                    features['closecharPerc75next'] = 1
            if temp > 0.9:
                features['charPerc90next'] = 1
                if (size - i) < tail_lines:
                    features['closecharPerc90next'] = 1

        mail_features.append(features)

    return mail_features
