from sklearn.svm import LinearSVC, SVC
from sklearn.metrics import accuracy_score, classification_report, precision_recall_fscore_support, confusion_matrix
from sklearn.preprocessing import LabelEncoder, StandardScaler
from keras.layers import LSTM, Activation, Dropout, Dense, Masking, GRU
from keras.layers.noise import GaussianNoise
from keras.models import Sequential
from sklearn import metrics
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import warnings
from keras.utils import np_utils, Sequence
from keras.regularizers import l2
from scripts.utils import AnnotatedEmails, AnnotatedEmail
from scripts.utils import denotation_types
from pprint import pprint
from scripts.FeatureRNN.features import mail2features
from sklearn.utils import compute_class_weight
from collections import Counter
from keras.callbacks import TensorBoard
from keras.initializers import RandomUniform
import time

cols = ['blank_line:0',
        'emailpattern:0',
        'lastline:0',
        'prevToLastLine:0',
        'containsPhonePattern:0',
        'signatureMarker:0',
        'signatureMarker2:0',
        'signatureMarker3:0',
        '5special:0',
        'namePattern:0',
        'quoteEnd:0',
        'containsSenderName_first:0',
        'containsSenderName_last:0',
        'containsSenderName_mail:0',
        'numTabs=1:0',
        'numTabs=2:0',
        'numTabs>=3:0',
        'numWords=1',
        'numWords=2',
        'numWords<=5',
        'numWords>5',
        'punctuation>20:0',
        'punctuation>50:0',
        'punctuation>90:0',
        'typicalMarker:0',
        'startWithPunct:0',
        'nextSamePunct:0',
        'prevSamePunct:0',
        'alphnum<90:0',
        'alphnum<50:0',
        'alphnum<10:0',
        # 'hasWord=bcc:0',  #
        # 'hasWord=cc:0',  #
        # 'hasWord=cell:0',  #
        # 'hasWord=date:0',  #
        # 'hasWord=fax:0',  #
        # 'hasWord=from:0',  #
        # 'hasWord=fwdby:0',  #
        # 'hasWord=fwdmsg:0',  #
        # 'hasWord=origmsg:0',  #
        # 'hasWord=phone:0',  #
        # 'hasWord=sent:0',  #
        # 'hasWord=subj:0',  #
        # 'hasWord=subject:0',  #
        # 'hasWord=to:0',  #
        'hasWord=sentby:0',
        # 'beginswithShape=Xx{2,8}\::0',  #
        # 'hasForm=^dd/dd/dddd dd:dd ww$:0',  #
        # 'containsForm=dd/dd/dddd dd:dd ww:0',  #
        # 'hasLDAPthings:0',  #
        # 'hasForm=^dd:dd:dd ww$:0'  #
        'endsWith=,',
        'endsWith=!',
        'endsWith=:',
        'startsWith=hi',
        'startsWith=dear',
        'startsWith=hey',
        'startsWith=facsimile',
        'startsWith=fax',
        'startsWith=phone',
        'startsWith=mail',
        'startsWith=cell',
        'startsWith=home',
        'containsSenderName_any:0',
        'containsMimeWord:0',
        'containsHeaderStart:0',
        'containsSignatureWord:0']


def flatten(lst):
    return [l for sub in lst for l in sub]


def to_array(lst, cols=None):
    df = pd.DataFrame(lst, columns=cols)
    df.fillna(0, inplace=True)
    return df.columns, np.nan_to_num(df.as_matrix(cols))


class MailBatches(Sequence):
    def __init__(self, x, y, batch_size, features, label_encoder, with_labels=True, with_weights=True):
        self.x = x
        self.y = y
        self.features = features
        self.batch_size = batch_size
        self.label_encoder = label_encoder
        self.cache = {}

        self.with_labels = with_labels
        self.with_weights = with_weights
        self.class_weights = []

        if y is not None:
            y_flat = flatten(y)
            self.class_weights = compute_class_weight('balanced', self.label_encoder.classes_, y_flat)
            # print(Counter(y_flat))
            # print(dict(zip(self.label_encoder.classes_, self.class_weights)))

    def __len__(self):
        return len(self.x) // self.batch_size

    def __getitem__(self, idx):
        if idx in self.cache:
            return self._return_value(*self.cache[idx])

        batch_x = self.x[self.batch_size * idx:self.batch_size * (idx + 1)]
        if self.y is not None:
            batch_y = self.y[self.batch_size * idx:self.batch_size * (idx + 1)]
        else:
            batch_y = [0] * len(batch_x)

        max_len = max([len(x) for x in batch_x])

        X = []
        Y = []
        W = []
        for xs, ys in zip(batch_x, batch_y):
            X.append(self._mask(self._as_array(xs), max_len))
            if self.y is not None:
                Y.append(self._mask(self._encode_labels(ys), max_len))
                W.append(self._mask(np.array([self.class_weights[y]
                                              for y in self.label_encoder.transform(ys)]), max_len))

        X = np.array(X)
        Y = np.array(Y)
        W = np.array(W)
        # print(idx, X.shape, Y.shape, W.shape)
        self.cache[idx] = (X, Y, W)

        return self._return_value(X, Y, W)

    def materialise(self):
        x = []
        y = []
        w = []

        tmp_with_weights = self.with_weights
        tmp_with_labels = self.with_labels
        self.with_weights = True
        self.with_labels = True

        for i in range(self.__len__()):
            if self.y is not None:
                tmpx, tmpy, tmpw = self.__getitem__(i)
                x.append(tmpx)
                y.append(tmpy)
                w.append(tmpw)
            else:
                x.append(self.__getitem__(i))

        self.with_weights = tmp_with_weights
        self.with_labels = tmp_with_labels

        return x, y, w

    def _return_value(self, X, Y, W):
        # if not self.with_weights:
        #    print(X[0])
        if self.y is not None:
            ret = [X]
            if self.with_labels:
                ret.append(Y)
            if self.with_weights:
                ret.append(W)
            return tuple(ret)
        else:
            return X

    def _as_array(self, lst):
        df = pd.DataFrame(lst, columns=self.features)
        df.fillna(0, inplace=True)
        return np.nan_to_num(df.as_matrix())

    def _encode_labels(self, lst):
        return np_utils.to_categorical(self.label_encoder.transform(lst),
                                       len(self.label_encoder.classes_))

    @staticmethod
    def _mask(arr, target_len, pre=False):
        zeros = np.zeros((target_len - arr.shape[0], arr.shape[1])) \
            if arr.ndim == 2 else np.zeros((target_len - len(arr),))

        if pre:
            return np.append(zeros, arr, 0)
        return np.append(arr, zeros, 0)

    def on_epoch_end(self):
        pass


class Model:
    def __init__(self, features, label_encoder, batch_size=10):
        self.batch_size = batch_size
        self.features = features
        self.label_encoder = label_encoder

        self.init_weights = None
        self.model = None

    def init_lstm_model(self):
        model = Sequential()
        model.add(Masking(mask_value=0.0,
                          input_shape=(None, len(self.features))))
        model.add(GaussianNoise(0.3))
        model.add(GRU(units=len(self.features),
                      # input_shape=(None, len(self.features)),
                      return_sequences=True,
                      kernel_initializer='glorot_uniform',
                      recurrent_initializer='orthogonal',
                      bias_initializer='zeros',
                      # kernel_regularizer=l2(0.1),
                      bias_regularizer=l2(0.2),
                      # recurrent_regularizer=l2(0.4),
                      # activity_regularizer=l2(0.4),
                      activation='tanh',
                      recurrent_activation='hard_sigmoid',
                      # dropout=0.2,
                      # recurrent_dropout=0.1,
                      name='rnn_layer1'))
        # model.add(LSTM(units=10,
        #                return_sequences=True,
        #                kernel_initializer='he_uniform',
        #                recurrent_initializer='orthogonal',
        #                kernel_regularizer=l2(0.01),
        #                recurrent_regularizer=l2(0.01),
        #                activation='tanh',
        #                dropout=0.3,
        #                # recurrent_dropout=0.1,
        #                name='rnn_layer2'))
        # model.add(Dense(len(self.labels),
        #                 kernel_initializer='he_uniform',
        #                 activity_regularizer=l2(0.05),
        #                 bias_regularizer=l2(0.01),
        #                 kernel_regularizer=l2(0.01),
        #                 activation='softmax',
        #                 name='output'))
        model.add(GRU(units=len(self.label_encoder.classes_),
                      return_sequences=True,
                      kernel_initializer='glorot_uniform',
                      recurrent_initializer='orthogonal',
                      bias_initializer='zeros',
                      # kernel_regularizer=l2(0.2),
                      # bias_regularizer=l2(0.2),
                      # recurrent_regularizer=l2(0.2),
                      # activity_regularizer=l2(0.2),
                      recurrent_activation='hard_sigmoid',
                      activation='softmax',
                      name='output'))

        model.compile(loss='categorical_crossentropy',  # 'msle',
                      optimizer='Adam',  # 'RMSprop',  # opts.Adadelta(),
                      sample_weight_mode='temporal',
                      metrics=['accuracy'])

        model.summary()

        self.init_weights = model.get_weights()
        self.model = model

    def reset_model(self):
        weights = self.init_weights
        if weights is None:
            weights = self.model.get_weights()
        weights = [np.random.permutation(w.flat).reshape(w.shape) for w in weights]
        self.model.set_weights(weights)

    def fit_model(self, x_train, y_train, epochs, x_test=None, y_test=None,
                  verbose=None, balanced=False, callback=None):
        train_generator = MailBatches(x_train, y_train, self.batch_size, self.features, self.label_encoder,
                                      with_labels=True, with_weights=balanced)

        val_data = None
        val_steps = None
        if x_test is not None and y_test is not None:
            if callback is None:
                val_data = MailBatches(x_test, y_test, self.batch_size, self.features, self.label_encoder,
                                       with_labels=True, with_weights=balanced)
                val_steps = len(val_data)
            else:
                test_generator = MailBatches(x_test, y_test, len(x_test), self.features, self.label_encoder,
                                             with_labels=True, with_weights=True)
                x, y, w = test_generator.materialise()
                val_data = (x[0], y[0], w[0]) if balanced else (x[0], y[0])

        return self.model.fit_generator(train_generator,
                                        steps_per_epoch=len(train_generator),
                                        epochs=epochs,
                                        verbose=verbose,
                                        validation_data=val_data,
                                        validation_steps=val_steps,
                                        callbacks=[callback] if callback is not None else None
                                        ).history

    def predict(self, x, y):
        test_generator = MailBatches(x, y, len(x), self.features, self.label_encoder,
                                     with_labels=True, with_weights=False)
        return self.model.predict_generator(test_generator, steps=len(test_generator))

        # def fit_model_continue(self, epochs, hist, verbose=None):
        #    newhist = self.fit_model(epochs, verbose)
        #    return {k: v + newhist[k] for k, v in hist.items()}


if __name__ == '__main__':
    zones = 5
    batch_size = 10
    epochs = 20
    features = cols
    labels = AnnotatedEmail.zone_labels(zones)
    # folder = "../../data/enron/annotated/"
    folder = "../../data/asf/annotated/"

    for perturb in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]:
        print('=============================================================')
        print('PERTURBATION:', perturb)
        emails = AnnotatedEmails(folder, mail2features, perturbation=perturb)
        print('loaded mails')

        X_train, X_test, X_eval = emails.features
        print('loaded features')

        if zones == 5:
            y_train, y_test, y_eval = emails.five_zones_labels
        elif zones == 3:
            y_train, y_test, y_eval = emails.three_zones_labels
        else:
            y_train, y_test, y_eval = emails.two_zones_labels
        print('loaded labels')

        # for zs, m in zip(y_train, emails.train_set):
        #    for z, l in zip(zs, m.lines):
        #        if z == ['Body', 'Header', 'Body/Signature', 'Body/Intro', 'Body/Outro'][2]:
        #            print(l)

        label_encoder = LabelEncoder()
        label_encoder.fit(labels)
        le = label_encoder
        class_weights = compute_class_weight('balanced', le.classes_, flatten(y_train))
        print(class_weights)
        if perturb == 0.0 and True:
            model = Model(features, label_encoder, batch_size=batch_size)
            model.init_lstm_model()
            model.fit_model(X_train, y_train, epochs=epochs, x_test=X_test, y_test=y_test, verbose=0, balanced=True, )
            # callback=TensorBoard(log_dir='./logs/' + time.strftime('%Y-%m-%d_%H-%M'),
            #                    write_images=True, histogram_freq=1))

        Y_pred = model.predict(X_test, y_test)

        y_pred = []
        y_pred_p = []
        a = True
        for m, mm in zip(Y_pred, X_test):
            # if a:
            #    a = False
            #    print(m.shape, len(mm))
            #    for w, l in zip(m[0:len(mm)], emails.test_set[0].lines):
            #        print(list(w), label_encoder.inverse_transform([w.argmax()])[0], ')', l[:100])
            # print(list(m)[0:len(mm)])
            # y_pred += list(m.argmax(axis=1))[len(m)-len(mm):]  # [0:len(mm)]
            # y_pred_p += list(m)[len(m)-len(mm):]  # [0:len(mm)]
            y_pred += list(m.argmax(axis=1))[0:len(mm)]
            y_pred_p += list(m)[0:len(mm)]

        # a = le.transform(flatten(y_test))
        a = flatten(y_test)
        b = label_encoder.inverse_transform(y_pred)

        # pprint(list(zip(a, b)))
        # pprint(list(zip(a, y_pred_p)))

        print('Accuracy: ', accuracy_score(a, b))
        print(classification_report(a, b, target_names=label_encoder.classes_))
        print('Accuracy (weighted): ', accuracy_score(a, b, sample_weight=[class_weights[s] for s in le.transform(a)]))
        print(classification_report(a, b, target_names=le.classes_, sample_weight=[class_weights[s] for s in le.transform(a)]))
        # pprint(precision_recall_fscore_support(b, a))
        print(label_encoder.classes_)
        print(confusion_matrix(a, b, labels=label_encoder.classes_))


# self.X_train = None
# self.X_test = None
# self.X_eval = None
# self.X_train_nested = None
# self.X_test_nested = None
# self.X_eval_nested = None
# self.y_train = None
# self.y_test = None
# self.y_eval = None
# self.Y_train = None
# self.Y_test = None
# self.Y_eval = None
# self.y_train_nested = None
# self.y_test_nested = None
# self.y_eval_nested = None
# self.Y_train_nested = None
# self.Y_test_nested = None
# self.Y_eval_nested = None

# def set_x(self, train, test, eval):
#     self.X_train = to_array(flatten(train), cols)
#     self.X_test = to_array(flatten(test), cols)
#     self.X_eval = to_array(flatten(eval), cols)
#
#     self.X_train_nested = [to_array(m, cols) for m in train]
#     self.X_test_nested = [to_array(m, cols) for m in test]
#     self.X_eval_nested = [to_array(m, cols) for m in eval]
#
# def set_y(self, train, test, eval):
#     n_classes = len(self.label_encoder.classes_)
#     self.y_train = self.label_encoder.transform(flatten(train))
#     self.y_test = self.label_encoder.transform(flatten(test))
#     self.y_eval = self.label_encoder.transform(flatten(eval))
#
#     self.Y_train = np_utils.to_categorical(self.y_train, n_classes)
#     self.Y_test = np_utils.to_categorical(self.y_test, n_classes)
#     self.Y_eval = np_utils.to_categorical(self.y_eval, n_classes)
#
#     self.y_train_nested = [self.label_encoder.transform(y) for y in train]
#     self.y_test_nested = [self.label_encoder.transform(y) for y in test]
#     self.y_eval_nested = [self.label_encoder.transform(y) for y in eval]
#
#     self.Y_train_nested = [np_utils.to_categorical(y, n_classes) for y in self.y_train_nested]
#     self.Y_test_nested = [np_utils.to_categorical(y, n_classes) for y in self.y_test_nested]
#     self.Y_eval_nested = [np_utils.to_categorical(y, n_classes) for y in self.y_eval_nested]
