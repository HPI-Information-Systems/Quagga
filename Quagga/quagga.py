import keras.backend as K
from keras_contrib.utils import save_load_utils
from keras.models import model_from_json
from keras.models import Model
from keras.layers import Masking, GRU, Input, Bidirectional
from keras_contrib.layers import CRF
import numpy as np
from sklearn.preprocessing import LabelEncoder
import os.path
import tensorflow as tf

line_embedding_size = 32


def load_keras_model(path, model=None):
    with open(os.path.abspath(path + '.json'), 'r') as jf:
        json_model = jf.read()
    if model is None:
        model = model_from_json(json_model)
        # model.summary()
    # print(model.get_weights()[0])
    try:
        save_load_utils.load_all_weights(model, os.path.abspath(path + '.hdf5'))
    except KeyError:
        model.load_weights(os.path.abspath(path + '.hdf5'))
    # print(model.get_weights()[0])
    return model


def get_mail_model_five():
    output_size = 5
    in_mail = Input(shape=(None, line_embedding_size * 2), dtype='float32')
    mask = Masking()(in_mail)
    hidden = GRU(32,
                 return_sequences=True,
                 implementation=0)(mask)
    crf = CRF(output_size, sparse_target=False)
    output = crf(hidden)

    model = Model(inputs=in_mail, outputs=output)

    # model.compile(loss=crf.loss_function, optimizer='adam', metrics=[crf.accuracy])
    return model


def get_mail_model_two():
    output_size = 2
    in_mail = Input(shape=(None, line_embedding_size), dtype='float32')

    mask = Masking()(in_mail)
    hidden = Bidirectional(GRU(32 // 2,
                               return_sequences=True,
                               implementation=0))(mask)
    crf = CRF(output_size, sparse_target=False)  # , test_mode='marginal', learn_mode='marginal')
    output = crf(hidden)

    model = Model(inputs=in_mail, outputs=output)
    # model.compile(loss=crf.loss_function, optimizer='adam', metrics=[crf.accuracy])
    return model


def get_embedding_function(model):
    model_in = [model.input]
    embedding_func = K.function(model_in + [K.learning_phase()], [model.layers[-2].output])

    def lambdo(x):
        return embedding_func([x, 0.])[0]

    return lambdo


enron_two_zone_line_b = load_keras_model('models/two_zones/enron_line_model_b')
enron_two_zone_model = load_keras_model('models/two_zones/enron_model', model=get_mail_model_two())
enron_five_zone_line_a = load_keras_model('models/five_zones/enron_line_model_a')
enron_five_zone_line_b = load_keras_model('models/five_zones/enron_line_model_b')
enron_five_zone_model = load_keras_model('models/five_zones/enron_model', model=get_mail_model_five())
asf_two_zone_line_b = load_keras_model('models/two_zones/asf_line_model_b')
asf_two_zone_model = load_keras_model('models/two_zones/asf_model', model=get_mail_model_two())
asf_five_zone_line_a = load_keras_model('models/five_zones/asf_line_model_a')
asf_five_zone_line_b = load_keras_model('models/five_zones/asf_line_model_b')
asf_five_zone_model = load_keras_model('models/five_zones/asf_model', model=get_mail_model_five())

enron_five_zone_line_a_func = get_embedding_function(enron_five_zone_line_a)
enron_five_zone_line_b_func = get_embedding_function(enron_five_zone_line_b)
enron_two_zone_line_b_func = get_embedding_function(enron_two_zone_line_b)
asf_five_zone_line_a_func = get_embedding_function(asf_five_zone_line_a)
asf_five_zone_line_b_func = get_embedding_function(asf_five_zone_line_b)
asf_two_zone_line_b_func = get_embedding_function(asf_two_zone_line_b)

two_encoder = LabelEncoder().fit(['Body', 'Header'])
five_encoder = LabelEncoder().fit(['Body', 'Header', 'Body/Signature', 'Body/Intro', 'Body/Outro'])

char_index = list(' '
                  'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                  'abcdefghijklmnopqrstuvwxyz'
                  '0123456789'
                  '@€-_.:,;#\'+*~\?}=])[({/&%$§"!^°|><´`\n')
num_possible_chars = len(char_index)
line_length = 80

graph = tf.get_default_graph()

def embed(lines, embedding_functions=None):
    x = np.zeros((len(lines), line_length, num_possible_chars + 1))

    for i, line in enumerate(lines):
        for j, c in enumerate(line):
            if j >= line_length:
                break
            x[i][j][char_index.index(c) + 1 if c in char_index else 0] = 1

    if embedding_functions is None:
        return x

    x = np.concatenate([embedding_function(x) for embedding_function in embedding_functions], axis=1)

    return x


def prettify_prediction(y, text_lines, label_encoder):
    labels = label_encoder.classes_
    ret = []
    for yi, line in zip(y, text_lines):
        tmp = {
            'text': line,
            'predictions': {}
        }
        for li, label in enumerate(labels):
            tmp['predictions'][label] = yi[li]
        ret.append(tmp)
    return ret


def get_predictions(text, with_crf=True, zones=2, trainset='enron'):
    text_raw = text
    text_lines = text_raw.split('\n')

    if zones not in [2, 5]:
        raise ValueError('Only trained for 2 and 5 zone predictions!')
    if trainset not in ['enron', 'asf']:
        raise ValueError("Only trained on 'enron' and 'asf' corpus!")
    if with_crf not in [True, False]:
        raise ValueError("Invalid value for with_crf. Has to be bool!")
    global graph
    with graph.as_default():
        if zones == 5:
            if trainset == 'enron':
                func_a = enron_five_zone_line_a_func
                func_b = enron_five_zone_line_b_func
                model = enron_five_zone_model
                embedding_a = enron_five_zone_line_a
            else:
                func_a = asf_five_zone_line_a_func
                func_b = asf_five_zone_line_b_func
                model = asf_five_zone_model
                embedding_a = asf_five_zone_line_a

            if with_crf:
                text_embedded = embed(text_lines, [func_a, func_b])
                y = model.predict(np.array([text_embedded])).tolist()[0]
                return y, text_lines, five_encoder
            else:
                return embedding_a.predict(embed(text_lines)).tolist(), text_lines, five_encoder

        else:
            if trainset == 'enron':
                func_b = enron_two_zone_line_b_func
                model = enron_two_zone_model
                embedding_b = enron_two_zone_line_b
            else:
                func_b = asf_two_zone_line_b_func
                model = asf_two_zone_model
                embedding_b = asf_two_zone_line_b

            if with_crf:
                text_embedded = embed(text_lines, [func_b])
                y = model.predict(np.array([text_embedded])).tolist()[0]
                return y, text_lines, two_encoder
            else:
                return embedding_b.predict(embed(text_lines)).tolist(), text_lines, two_encoder
