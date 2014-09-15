import requests
import os
import json
from urlparse import urlparse

storedir = os.path.join(os.path.dirname(__file__), 'fixtures')
testsdir = os.path.join(storedir, 'records')
savedir = os.path.join(storedir, 'saved_requests')


class WebtestParams(object):

    def __init__(self, description, url, method='GET', http_host=None, extra_headers={}, body=None, **kwdargs):
        self.title = description
        self.url = url
        self.method = method
        if extra_headers:
            self.headers = json.loads(extra_headers)
        else:
            self.headers = {}
        if body:
            self.body = json.loads(body)
        else:
            self.body = None
        if http_host:
            self.headers['Host'] = http_host

def parse(txt, host):
    lines = txt.split("\n")
    print lines
    description = lines.pop(0)
    print description
    url = lines.pop(0)
    kwdargs = {}
    for line in lines:
        if line.startswith('#'):
            continue
        try:
            (k, v) = [l.strip() for l in line.split(':')]
            kwdargs[k] = v
        except:
            print("malformed line {}".format(line))

    parsed = urlparse(url)
    http_host = parsed.netloc.split(':')[0]
    if http_host != host:
        url.replace(http_host,host)
        kwdargs['http_host'] = http_host
    return WebtestParams(description, url, **kwdargs)



class WebtestRecord(object):
    """
    A webtest record class. It is used to either store a record, or to fetch it from the repository
    """
    _headers_blacklist = ['set-cookie', 'expires', 'x-varnish', 'x-cache']

    def __init__(self, name, host):
        self.record = name
        self.filepath = os.path.join(testsdir, name)
        self.savepath = os.path.join(savedir, '{}_{}'.format(host, name))
        with open(self.filepath,'r') as fh:
            self.params = parse(fh.read(), host)

    def _fetch(self):
        try:
            r = requests.request(
                self.params.method,
                self.params.url,
                headers = self.params.headers,
                data = self.params.body
            )
            resp = { 'status': r.status_code}

            if 'content-length' in r.headers:
                resp['length'] = int(r.headers['content-length'])
            else:
                resp['length'] = len(r.text)

            for (k,v) in r.headers.iteritems():
                if k in self._headers_blacklist:
                    continue
                resp[k] = v

            return resp
        except:
            print("There was a problem with your request, see details")
            raise


    def save(self):
        resp = self._fetch()
        with open(self.savepath, 'w') as fh:
            json.dump(resp, fh)

    def load(self):
        with open(self.savepath, 'r') as fh:
            resp = json.load(fh)
        return resp

    def test(self):
        original = self.load()
        resp = self._fetch()
        len_change = False
        orig_keys = set(original.keys())
        resp_keys = set(resp.keys())
        only_in_orig = orig_keys - resp_keys
        only_in_resp = resp_keys - orig_keys
        return (only_in_orig, only_in_resp, original, resp)
