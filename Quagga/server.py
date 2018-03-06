from flask import Flask, request
from flask.json import jsonify
from .quagga import prettify_prediction, get_predictions


def prediction2response(y, text_lines, label_encoder):
    ret = prettify_prediction(y, text_lines, label_encoder)
    return jsonify(ret)


app = Flask(__name__)


@app.route('/index')
def root():
    return app.send_static_file('index.html')


@app.route('/five', methods=['POST'])
def five():
    data = request.get_json()

    prediction = get_predictions(data['rawText'],
                                 with_crf=(data.get('model', '') == 'crf'),
                                 zones=5,
                                 trainset=data.get('trainedOn', 'enron'))
    return prediction2response(*prediction)


@app.route('/two', methods=['POST'])
def two():
    data = request.get_json()
    prediction = get_predictions(data['rawText'],
                                 with_crf=(data.get('model', '') == 'crf'),
                                 zones=2,
                                 trainset=data.get('trainedOn', 'enron'))
    return prediction2response(*prediction)


if __name__ == '__main__':
    # FLASK_APP=server.py flask run
    app.run()
