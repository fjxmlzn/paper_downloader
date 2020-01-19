import os
import traceback
import ssl

try:
    # Try importing for Python 3
    # pylint: disable-msg=F0401
    # pylint: disable-msg=E0611
    from urllib.request import HTTPCookieProcessor, Request, build_opener, \
        HTTPSHandler
    from http.cookiejar import MozillaCookieJar
except ImportError:
    # Fallback for Python 2
    from urllib2 import Request, build_opener, HTTPCookieProcessor, \
        HTTPSHandler
    from cookielib import MozillaCookieJar

__author__ = 'Zinan Lin'
__email__ = 'zinanl@andrew.cmu.edu'
__credits__ = ['Christian Kreibich']


class Downloader(object):
    def __init__(self, args):
        self.cjar = MozillaCookieJar()

        self.debug = args.debug
        self.user_agent = args.user_agent
        self.cookie_file = args.cookie_file

        if os.path.exists(self.cookie_file):
            try:
                self.cjar.load(self.cookie_file, ignore_discard=True)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                self.cjar = MozillaCookieJar()
                if args.debug:
                    traceback.print_exc()

        # Fix from:
        # https://stackoverflow.com/questions/19268548/python-ignore-certificate-validation-urllib2
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        self.opener = build_opener(
            HTTPSHandler(context=ctx), HTTPCookieProcessor(self.cjar))

    def _get_http_response(self, url):
        try:
            req = Request(url=url, headers={'User-Agent': self.user_agent})
            hdl = self.opener.open(req)
            html = hdl.read()

            return html
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            if self.debug:
                traceback.print_exc()
            return None

    def download(self, url, save_path):
        # simple fix for ACM
        if "dl.acm.org/doi/pdf" in url and not url.endswith("?download=true"):
            url += "?download=true"
        content = self._get_http_response(url)
        if content is None:
            return False
        else:
            with open(save_path, 'wb') as f:
                f.write(content)
            return True
