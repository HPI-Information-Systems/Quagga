"""Collins Perceptron
This is a wrapper for edu.cmu.minorthird.classify.sequential.CollinsPerceptronLearner
"""
import subprocess
import os
import re

FILE_IN = os.path.abspath('tmpfiles/data-in.dat')
FILE_OUT = os.path.abspath('tmpfiles/data-out.dat')
FILE_MODEL = os.path.abspath('tmpfiles/model.cls')

# Usage:
#   train <int:historylen> <str:data-file> <str:model-file> <int:epochs>
#   test  <int:historylen> <str:data-file> <str:model-file> <str:out-file>
# java -cp mtwrap/out/artifacts/mtwrap_jar/mtwrap.jar edu.hpi.minorthird.wrapper.Main test 5 in.dat model.cls out.dat
MT_WRAP_LIB = os.path.abspath('mtwrap/out/artifacts/mtwrap_jar/mtwrap.jar')


def _to_file(documents, nested_labels):
    f = open(FILE_IN, 'w')
    f.truncate()
    for i, (doc, labels) in enumerate(zip(documents, nested_labels)):
        for x, y in zip(doc, labels):
            line = 'k mail' + str(i) + ' '
            line += str(y) + ' '
            for feature, value in x.items():
                line += feature + '=' + str(value) + ' '
            f.write(line + '\n')
        f.write('*' + '\n')
    f.close()


def _from_file():
    ret = []
    with open(FILE_OUT, 'r') as f:
        pattern = re.compile(
            r'^\[Class: (?P<label>[A-Za-z/]+) (?P<confidence>-?\d+\.[0-9E]+)\].*\[compact instance/(?P<mail>\w+):')
        for line in f.readlines():
            m = pattern.search(line)
            ret.append((m.group('mail'), m.group('label'), float(m.group('confidence'))))
    return ret


def _result2predict(label, confidence, labels):
    if labels is not None:
        tmp = [0.0] * len(labels)
        tmp[labels.index(label)] = confidence
        return tmp
    return label


class CollinsPerceptron:
    def __init__(self, size_history, model_file):
        self.size_history = size_history
        self.model_file = model_file

    def fit(self, X, y, n_epochs):
        _to_file(X, y)
        try:
            p = subprocess.run(['java', '-cp', MT_WRAP_LIB,
                                'edu.hpi.minorthird.wrapper.Main', 'train',
                                str(self.size_history), FILE_IN, FILE_MODEL, str(n_epochs)],
                               check=True)
        except subprocess.SubprocessError as e:
            print(e)
            pass

    def predict(self, X, y=None, labels=None):
        if y is None:
            y = ['Body'] * len(X)

        _to_file(X, y)

        try:
            p = subprocess.run(['java', '-cp', MT_WRAP_LIB,
                                'edu.hpi.minorthird.wrapper.Main', 'test',
                                str(self.size_history), FILE_IN, FILE_MODEL, FILE_OUT],
                               check=True)

            result = _from_file()

            ret = []
            instance = []
            last = None

            for mail, label, confidence in result:
                if last is None:
                    last = mail

                if last != mail:
                    ret.append(instance)
                    instance = []
                    last = mail

                instance.append(_result2predict(label, confidence, labels))
            ret.append(instance)

            return ret

        except subprocess.SubprocessError as e:
            print(e)
            raise e
