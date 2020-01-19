import copy
import re
import json

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from six.moves.urllib.request import urlopen
import numpy as np

__author__ = 'Zinan Lin'
__email__ = 'zinanl@andrew.cmu.edu'


def _get_average_num_word(titles):
    return np.mean([len(t.split()) for t in titles])


def _get_average_frac_eng(titles):
    filter_ = '([a-zA-Z ])'
    return np.mean([float(len(re.findall(filter_, t))) / max(1, len(t))
                    for t in titles])


def _get_frac_keywords(titles,
                       keywords=['workshop', 'tutorials', 'session',
                                 'location']):
    cnt = 0
    for title in titles:
        title = title.lower()
        found = False
        for keyword in keywords:
            if keyword in title:
                found = True
                break
        if found:
            cnt += 1
    return float(cnt) / len(titles)


def _to_string(key):
    return json.dumps(key)


def _to_title(key):
    return ' '.join(unicode(key).split())


def paper_list_from_url(url, keys=None, attrs=[]):
    html = urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')

    contents = {}

    def id_(node):
        result = [str(node.name)]
        for attr in attrs:
            if node.has_attr('class'):
                result.append(node['class'])
            else:
                result.append(None)
        return result

    def search(node, parents):
        parents = copy.deepcopy(parents)
        parents.append(id_(node))
        for child in getattr(node, 'children', []):
            if isinstance(child, NavigableString):
                if _to_string(parents) not in contents:
                    contents[_to_string(parents)] = []
                contents[_to_string(parents)].append(_to_title(child))
            else:
                search(child, parents)
    search(soup, [])

    if keys is None:
        keys = []
        for key in contents:
            average_num_word = _get_average_num_word(contents[key])
            average_frac_eng = _get_average_frac_eng(contents[key])
            frac_keywords = _get_frac_keywords(contents[key])
            if (average_num_word >= 6 and average_num_word <= 30 and
                    average_frac_eng >= 0.90 and
                    frac_keywords <= 0.1 and
                    len(contents[key]) >= 3):
                keys.append(key)

    papers = []
    for key in keys:
        papers.extend(contents[key])

    return papers, keys, contents
