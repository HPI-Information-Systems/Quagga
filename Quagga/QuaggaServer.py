from flask import Flask, request
from flask.json import jsonify



from Utils.ModelBuilder import ModelBuilder
from Utils.EmailReader import ListReaderExtractedBodies
from Quagga import Quagga


quagga = Quagga(ListReaderExtractedBodies(''))


app = Flask(__name__)


@app.route('/index')
def root():
    return app.send_static_file('index.html')


@app.route('/five', methods=['POST'])
def five():
    data = request.get_json()
    model_builder = ModelBuilder(with_crf=(data.get('model', '') == 'crf'), zones=5, trainset=data.get('trainedOn', 'enron'))
    #quagga = Quagga(ListReaderExtractedBodies(data['rawText']), model_builder=model_builder)
    quagga._build_model(model_builder)
    prediction = quagga._predict(data.get('rawText'))
    return jsonify(prediction)


@app.route('/two', methods=['POST'])
def two():
    data = request.get_json()
    model_builder = ModelBuilder(with_crf=(data.get('model', '') == 'crf'), zones=2, trainset=data.get('trainedOn', 'enron'))
    #quagga = Quagga(ListReaderExtractedBodies(data['rawText']), model_builder=model_builder)
    quagga._build_model(model_builder)
    prediction = quagga._predict(data.get('rawText'))

    return jsonify(prediction)


if __name__ == '__main__':
    # export FLASK_APP=QuaggaServer.py
    # flask run
    app.run()
