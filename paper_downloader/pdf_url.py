import numpy as np

from .scholar.scholar import ScholarQuerier
from .scholar.scholar import SearchScholarQuery
from .scholar.scholar import ClusterScholarQuery
from .scholar.scholar import ScholarConf
from .constant import PDF_URL
from .constant import PAPER_TITLE

__author__ = 'Zinan Lin'
__email__ = 'zinanl@andrew.cmu.edu'


def _longest_common_substring(s1, s2):
    s1 = s1.lower()
    s2 = s2.lower()
    ls1 = len(s1)
    ls2 = len(s2)
    f = np.zeros((ls1 + 1, ls2 + 1))
    for i in range(1, ls1 + 1):
        for j in range(1, ls2 + 1):
            f[i, j] = max(f[i - 1, j], f[i, j - 1])
            if s1[i - 1] == s2[j - 1]:
                f[i, j] = max(f[i, j], f[i - 1, j - 1] + 1)
    return f[ls1, ls2] / max(ls1, ls2)


def gscholar_pdf_url_from_title(title, eps=1e-6):
    querier = ScholarQuerier()
    query = SearchScholarQuery()
    query.set_phrase(title)
    query.set_num_page_results(ScholarConf.MAX_PAGE_RESULTS)
    querier.send_query(query)

    articles = querier.articles

    scores = []
    cluster_ids = []
    pdf_urls = []
    titles = []

    for art in articles:
        if art['title'] is not None and art['cluster_id'] is not None:
            scores.append(_longest_common_substring(art['title'], title))
            cluster_ids.append(art['cluster_id'])
            titles.append(art['title'])
            pdf_urls.append(art['url_pdf'])
    papers = []
    if len(scores) > 0:
        sort_list = np.argsort(scores)[::-1]
        for best_id in range(len(sort_list)):
            if np.abs(scores[sort_list[best_id]] - scores[sort_list[0]]) > eps:
                break
            cluster_id = cluster_ids[best_id]
            if pdf_urls[best_id] is not None:
                papers.append({
                    PAPER_TITLE: titles[best_id],
                    PDF_URL: pdf_urls[best_id]})

            query = ClusterScholarQuery(cluster=cluster_id)
            querier.send_query(query)
            articles = querier.articles
            for art in articles:
                if art['title'] is not None and art['url_pdf'] is not None:
                    papers.append({
                        PAPER_TITLE: art['title'],
                        PDF_URL: art['url_pdf']})
    return papers
