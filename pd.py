import argparse
import os
import shutil
import json
import time
import re
import resource
from encodings import hex_codec

from tqdm import tqdm
from PyPDF2 import PdfFileReader, PdfFileWriter

from paper_downloader.constant import CONF_URL_FILE_SUFFIX
from paper_downloader.constant import PDF_URL_FILE_SUFFIX
from paper_downloader.constant import PAPER_LIST_FILE_SUFFIX
from paper_downloader.constant import CONF_NAME
from paper_downloader.constant import CONF_URL
from paper_downloader.constant import CONF_ELE
from paper_downloader.constant import CONF_ATTRS
from paper_downloader.constant import PAPER_TITLE
from paper_downloader.constant import PAPER_LINKS
from paper_downloader.constant import PDF_URL
from paper_downloader.paper_list import paper_list_from_url
from paper_downloader.pdf_url import gscholar_pdf_url_from_title
from paper_downloader.scholar.scholar import ScholarConf
from paper_downloader.scholar.scholar import ScholarUtils
from paper_downloader.downloader import Downloader

__author__ = 'Zinan Lin'
__email__ = 'zinanl@andrew.cmu.edu'


def get_conf_url_path(args):
    if args.conference is None:
        root_folder = args.temp_folder
    else:
        root_folder = args.url_folder
    return os.path.join(
        root_folder, str(args.conference) + CONF_URL_FILE_SUFFIX)


def get_pdf_url_path(args):
    if args.conference is None:
        root_folder = args.temp_folder
    else:
        root_folder = args.url_folder
    return os.path.join(
        root_folder, str(args.conference) + PDF_URL_FILE_SUFFIX)


def get_paper_list_path(args):
    if args.conference is None:
        root_folder = args.temp_folder
    else:
        root_folder = args.url_folder
    return os.path.join(
        root_folder, str(args.conference) + PAPER_LIST_FILE_SUFFIX)


def get_paper_pdf_path(args, paper):
    if args.store:
        root_folder = args.pdf_folder
    else:
        root_folder = args.temp_folder
    file_name = re.sub('[^a-zA-Z0-9 ]+', '', paper)
    return os.path.join(root_folder, file_name + '.pdf')


def get_merged_pdf_path(args):
    return os.path.join(args.pdf_folder, args.merge_file)


def conf_url_exists(args):
    return os.path.exists(get_conf_url_path(args))


def pdf_url_exists(args):
    return os.path.exists(get_pdf_url_path(args))


def paper_list_exists(args):
    return os.path.exists(get_paper_list_path(args))


def process_conf_url(args):
    print('Pre-Parse conference webpage')

    if args.url is None:
        raise Exception('Please specify url')
    data = {
        CONF_NAME: str(args.conference),
        CONF_URL: args.url}
    _, keys, contents = paper_list_from_url(
        args, args.url, args.ele, args.attrs)
    data[CONF_ELE] = keys
    data[CONF_ATTRS] = args.attrs
    path = get_conf_url_path(args)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
    print('Conference webpage parsing results saved to: {}'.format(path))

    if args.debug:
        str_ = ''
        for key in contents:
            str_ += '---\n'
            str_ += ('If following strings are paper titles, add\n{}\nto {}'
                     ' in {}\n\n'.format(
                         json.dumps(key, indent=4), CONF_ELE, path))
            for i, title in enumerate(contents[key]):
                str_ += '{}: '.format(i + 1)
                str_ += title
                str_ += '\n'
            str_ += '---\n'

        with open(args.debug_file, 'wb') as f:
            f.write(str_.encode('utf-8'))


def process_paper_list(args):
    print('Post-Parse conference webpage')

    conf_url_path = get_conf_url_path(args)
    with open(conf_url_path, 'r') as f:
        data = json.load(f)
    print('Using {}'.format(conf_url_path))

    conf_url = data[CONF_URL]
    conf_ele = data[CONF_ELE]
    conf_attrs = data[CONF_ATTRS]
    papers, _, _ = paper_list_from_url(args, conf_url, conf_ele, conf_attrs)
    print('Found {} papers'.format(len(papers)))

    paper_list_path = get_paper_list_path(args)
    with open(paper_list_path, 'w') as f:
        json.dump(papers, f, indent=4)

    print('Paper list saved to: {}'.format(paper_list_path))


def process_pdf_url(args):
    print('Get PDF URLs')

    if args.fix_pdf_url and pdf_url_exists(args):
        pdf_url_path = get_pdf_url_path(args)
        with open(pdf_url_path, 'r') as f:
            old_data = json.load(f)
        print('Found {}'.format(pdf_url_path))
        papers = [t[PAPER_TITLE] for t in old_data]
    else:
        paper_list_path = get_paper_list_path(args)
        with open(paper_list_path, 'r') as f:
            papers = json.load(f)
        old_data = []
        print('Using {}'.format(paper_list_path))

    def search(paper, data):
        for i in range(len(data)):
            if data[i][PAPER_TITLE] == paper:
                return data[i][PAPER_LINKS]
        return []

    data = []
    for paper in tqdm(papers):
        links = search(paper, old_data)
        if len(links) == 0:
            links = gscholar_pdf_url_from_title(paper)
            time.sleep(args.delay)
        data.append({
            PAPER_TITLE: paper,
            PAPER_LINKS: links})

    pdf_url_path = get_pdf_url_path(args)
    with open(pdf_url_path, 'w') as f:
        json.dump(data, f, indent=4)
    print('PDF links saved to: {}'.format(pdf_url_path))


def download_papers(args):
    print('Download papers')

    pdf_url_path = get_pdf_url_path(args)
    with open(pdf_url_path, 'r') as f:
        papers = json.load(f)
    print('Using {}'.format(pdf_url_path))

    downloader = Downloader(args)

    for paper in tqdm(papers):
        success = False
        path = get_paper_pdf_path(args, paper[PAPER_TITLE])
        if os.path.exists(path):
            print('Skip: {}'.format(paper[PAPER_TITLE].encode('utf-8')))
            success = True
        else:
            for item in paper[PAPER_LINKS]:
                if downloader.download(item[PDF_URL], path):
                    success = True
                    break
        if not success:
            print('Failed to download: {}'.format(paper))


def merge_papers(args):
    print('Merge papers')

    if len(args.merge) == 0:
        raise Exception('Please specify merge')

    pdf_url_path = get_pdf_url_path(args)
    with open(pdf_url_path, 'r') as f:
        papers = json.load(f)
    print('Using {}'.format(pdf_url_path))

    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(
        resource.RLIMIT_NOFILE, (max(soft, len(papers) + 10), hard))

    writer = PdfFileWriter()
    file_steams = []
    for paper in tqdm(papers):
        path = get_paper_pdf_path(args, paper[PAPER_TITLE])
        if os.path.exists(path):
            f = open(path, 'rb')
            file_steams.append(f)
            reader = PdfFileReader(f, strict=False)
            for page in args.merge:
                if page >= 1 and page <= reader.getNumPages():
                    writer.addPage(reader.getPage(page - 1))
                else:
                    print('Skip: {} page of {}'.format(
                        page, paper[PAPER_TITLE].encode('utf-8')))
        else:
            print('Missing: {}'.format(paper[PAPER_TITLE]))

    path = get_merged_pdf_path(args)
    with open(path, 'wb') as f:
        writer.write(f)

    for f in file_steams:
        f.close()

    print('Merged PDF saved to: {}'.format(path))


def create_url_folder(args):
    if not os.path.exists(args.url_folder):
        os.makedirs(args.url_folder)


def create_temp_folder(args):
    if not os.path.exists(args.temp_folder):
        os.makedirs(args.temp_folder)


def create_pdf_folder(args):
    if not os.path.exists(args.pdf_folder):
        os.makedirs(args.pdf_folder)


def clean_temp_folder(args):
    shutil.rmtree(args.temp_folder)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Paper downloader',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-u', '--url',
        help='url of the paper list',
        type=str)
    parser.add_argument(
        '-e', '--ele',
        help='UI element path for finding the paper titles',
        type=str,
        action='append')
    parser.add_argument(
        '-a', '--attrs',
        help='UI element attributes for finding the paper titles',
        type=str,
        action='append',
        default=[])
    parser.add_argument(
        '-c', '--conference',
        help='name of the conference',
        type=str)
    parser.add_argument(
        '-s', '--store',
        help='store papers',
        action='store_true')
    parser.add_argument(
        '-m', '--merge',
        help='the page to be merged into a single PDF file',
        type=int,
        action='append')
    parser.add_argument(
        '--merge_file',
        help='the file name for the merged file',
        type=str,
        default='merged.pdf')
    parser.add_argument(
        '-d', '--delay',
        help='the delay (seconds) between queries to Google Scholar to avoid'
             'being banned',
        type=float,
        default=0.0)
    parser.add_argument(
        '--pdf_folder',
        help='the folder to store the downloaded/merged PDF files',
        type=str,
        default='pdf')
    parser.add_argument(
        '--url_folder',
        help='the folder to store the urls of conferences and pdfs',
        type=str,
        default='conf_url')
    parser.add_argument(
        '--temp_folder',
        help='the temporary folder',
        type=str,
        default='temp')
    parser.add_argument(
        '--debug',
        help='outputs for manual correcting paper list or url list',
        action='store_true')
    parser.add_argument(
        '--debug_file',
        help='the debug for storing debug outputs',
        type=str,
        default='debug.txt')
    parser.add_argument(
        '--fix_pdf_url',
        help='Querying the pdf links that are missing',
        action='store_true')
    parser.add_argument(
        '--user_agent',
        help='user agent for HTTP requests',
        type=str,
        default=('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:56.0) '
                 'Gecko/20100101 Firefox/56.0'))
    parser.add_argument(
        '--cookie_file',
        help='the path to the cookie.txt for HTTP requests',
        type=str,
        default=os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'cookies.txt'))

    args = parser.parse_args()

    if args.debug:
        ScholarConf.LOG_LEVEL = ScholarUtils.LOG_LEVELS['debug']
    ScholarConf.USER_AGENT = args.user_agent
    ScholarConf.COOKIE_JAR_FILE = args.cookie_file

    create_temp_folder(args)
    create_url_folder(args)
    create_pdf_folder(args)

    if not (conf_url_exists(args) or paper_list_exists(args) or
            pdf_url_exists(args)):
        process_conf_url(args)

    if not (paper_list_exists(args) or pdf_url_exists(args)):
        process_paper_list(args)

    if not pdf_url_exists(args) or args.fix_pdf_url:
        process_pdf_url(args)

    if args.store or (args.merge is not None):
        download_papers(args)

    if args.merge is not None:
        merge_papers(args)

    clean_temp_folder(args)
