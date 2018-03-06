import xml.etree.ElementTree as ET
from urllib import request, error, parse
from pprint import pprint
import os
import html
import random

base_url = 'http://mail-archives.apache.org/mod_mbox/'
target_folder = '../../data/asf/'
index_file = '../../data/asf/index.dat'
datasets = {
    'train': 250,
    'test': 100,
    'eval': 50
}
formats = {'mime': '', 'text': '/', 'mime/plain': '/1', 'mime/html': '/2'}
mail_format = formats['text']

k_dataset, k_list, k_page, k_year, k_month, k_depth, k_id, k_date, k_from, k_subject = range(10)

index = {}
stats = {}
with open(index_file, 'r') as file:
    for line in file:
        data = line.split('\t')
        index_key = data[k_dataset]
        if index_key not in index.keys():
            index[index_key] = []
        if index_key not in stats.keys():
            stats[index_key] = {
                'cnt': 0,
                'depths': {},
                'months': {}
            }
        index[index_key].append(data)

        stats[index_key]['cnt'] += 1
        stats[index_key]['depths'][data[k_depth]] = stats[index_key]['depths'].get(data[k_depth], 0) + 1
        stats[index_key]['months'][data[k_month]] = stats[index_key]['months'].get(data[k_month], 0) + 1

pprint(stats)
# http://mail-archives.apache.org/mod_mbox/flink-user/201709.mbox/raw/%3CCAMUrgW839XvMK%2BjkFFa2MQjqHLPJ-CXjC%2BG0--BxbvgKo_dY7w%40mail.gmail.com%3E/1

for dataset, num_samples in datasets.items():
    print('========================= ' + dataset.upper() + ' =========================')
    selected_indices = random.sample(range(stats[dataset]['cnt']), num_samples)
    print('Selected %d indices from %d mails: ' % (num_samples, stats[dataset]['cnt']), selected_indices)
    for selected_index in selected_indices:
        sample = index[dataset][selected_index]
        str_month = '%02d' % int(sample[k_month])
        print('> index: %d | id: %s | from: %s | date: %s | month: %s | depth: %s' % (selected_index, sample[k_id],
                                                                                      sample[k_from], sample[k_date],
                                                                                      str_month, sample[k_depth]))
        try:
            # 'http://mail-archives.apache.org/mod_mbox/flink-user/201709.mbox/ajax/%3CCAMUrgW_9%3DCvZPcreQWkY%3DBw_h%2BbT1Uzv_4d7_uiTyB%2BE0w0HQA%40mail.gmail.com%3E'
            url = 'http://mail-archives.apache.org/mod_mbox/' + sample[k_list] + '/' + \
                  sample[k_year] + str_month + '.mbox/ajax/' + parse.quote(sample[k_id])
            print(url)
            req = request.Request(url)
            with request.urlopen(req) as response:
                content = response.read()
                message = ET.fromstring(content)
                for child in message:
                    if child.tag == 'contents':
                        with open(os.path.join(target_folder, dataset, 'train_' + str(selected_index)), 'w') as file:
                            file.write(html.unescape(child.text))
                        break

        except error.HTTPError:
            print('FAILED HTTP request!')
