import xml.etree.ElementTree as ET
from urllib import request, error

year = '2017'
base_url = 'http://mail-archives.apache.org/mod_mbox/'
index_file = '../../data/asf/index.dat'
mailing_lists = {
    'train': 'lucene-solr-user',  # 250
    'test': 'spark-user',  # 100
    'eval': 'flink-user'  # 50
}

# dataset list page year month depth id date from subject
line_format = '%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s\t%s\t%s\n'

with open(index_file, 'w') as file:
    for dataset, mailing_list in mailing_lists.items():
        print('========================= ' + dataset.upper() + ' =========================')
        for month in range(12):
            str_month = '%02d' % (month + 1)
            print('------- month:' + str_month)
            page = 0
            has_next_page = True
            while has_next_page:
                try:
                    url = 'http://mail-archives.apache.org/mod_mbox/' + mailing_list + '/' + \
                          year + str_month + '.mbox/ajax/thread?' + str(page)
                    req = request.Request(url)

                    with request.urlopen(req) as response:
                        content = response.read()
                        index = ET.fromstring(content)

                        page += 1
                        current_page = index.attrib['page']
                        num_pages = index.attrib['pages']
                        has_next_page = page < int(num_pages)
                        print('> page ' + str(int(current_page) + 1) + '/' + num_pages + '  ' + url)
                        for message in index:
                            if message.attrib['linked'] == '1':
                                meta = {
                                    'depth': message.attrib['depth'],
                                    'id': message.attrib['id']
                                }
                                for field in message:
                                    meta[field.tag] = field.text

                                file.write(line_format % (dataset, mailing_list, current_page, year, (month + 1),
                                                          meta['depth'], meta['id'],
                                                          meta.get('date', year + '-' + str_month),
                                                          meta.get('from', '[unknown]'),
                                                          meta.get('subject', '[no-subject]')))
                except error.HTTPError:
                    print('FAILED')
                    has_next_page = False
