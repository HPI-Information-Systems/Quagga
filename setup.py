from setuptools import setup

with open("README.md", 'r') as f:
	long_description = f.read()

setup(
	name='Quagga',
	version='1.0',
	description='An email segmentation system',
	license="GPL",
	long_description=long_description,
	author='Tim Repke, Ben Hurdelhey',
	author_email='tim.repke@hpi.de',
	url="",
	packages=['Quagga', 'Quagga.Utils', 'Quagga.Examples'],
	package_data={'': ['models/*/*.json', 'models/*/*.hdf5', 'static/index.html']},
	install_requires=['absl-py==0.3.0', 'astor==0.7.1', 'autopep8==1.3.5', 'bleach==1.5.0', 'click==6.7',
	                  'cycler==0.10.0', 'Flask==1.0.2', 'gast==0.2.0', 'grpcio==1.14.0', 'h5py==2.8.0',
	                  'html5lib==0.9999999', 'itsdangerous==0.24', 'Jinja2==2.10', 'Keras==2.2.0',
	                  'kiwisolver==1.0.1', 'Markdown==2.6.11', 'MarkupSafe==1.0', 'matplotlib==2.2.2', 'numpy==1.14.5',
	                  'pandas==0.23.3', 'protobuf==3.6.0', 'pyparsing==2.2.0', 'python-dateutil==2.7.3', 'pytz==2018.5',
	                  'PyYAML==3.13', 'scikit-learn==0.19.2', 'scipy==1.1.0', 'six==1.11.0',
	                  'sklearn==0.0', 'tensorflow==1.5', 'termcolor==1.1.0',
	                  'Werkzeug==0.14.1', 'keras-contrib'],
	dependency_links=['git+https://www.github.com/keras-team/keras-contrib.git@f25c26665e990cfdf1da61a3de10a34d67f74b37#egg=keras-contrib'],
)
