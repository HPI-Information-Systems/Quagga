from flask import Flask, request
from flask.json import jsonify

import sys
sys.path.append('')
from quagga import Quagga
from quaggaModelBuilder import QuaggaModelBuilder

quagga = Quagga()


app = Flask(__name__)


@app.route('/index')
def root():
    return app.send_static_file('index.html')


@app.route('/five', methods=['POST'])
def five():
    data = request.get_json()
    quagga.build_model(model_builder=QuaggaModelBuilder(with_crf=(data.get('model', '') == 'crf'),
                                                        zones=5,
                                                        trainset=data.get('trainedOn', 'enron')))

    prediction = quagga._get_predictions(data['rawText'])
    return jsonify(prediction)


@app.route('/two', methods=['POST'])
def two():
    data = request.get_json()

    quagga.build_model(model_builder=QuaggaModelBuilder(with_crf=(data.get('model', '') == 'crf'),
                                                        zones=2,
                                                        trainset=data.get('trainedOn', 'enron')))

    prediction = quagga._get_predictions(data['rawText'])
    return jsonify(prediction)


if __name__ == '__main__':
    # cd Quagga/Quagga
    # export FLASK_APP=server/server.py
    # flask run
    app.run()
