import requests
import os
import json
from urlparse import urlparse
import yaml

storedir = os.path.join(os.path.dirname(__file__), 'fixtures')
testsdir = os.path.join(storedir, 'records')
savedir = os.path.join(storedir, 'saved_requests')


class WebtestParams(object):

    def __init__(self, description, url, method='GET', http_host=None, cookies = {}, headers={}, body=None, **kwdargs):
        self.title = description
        self.url = url
        self.method = method
        self.cookies = cookies
        self.headers = headers
        self.body = body
        if http_host:
            self.headers['Host'] = http_host

def parse(txt, host):
    record = yaml.load(txt)
    description = record['description']
    url = record['url']
    del record['description']
    del record['url']
    parsed = urlparse(url)
    http_host = parsed.netloc.split(':')[0]
    if http_host != host:
        url.replace(http_host,host)
        record['http_host'] = http_host
    return WebtestParams(description, url, **record)



class WebtestRecord(object):
    """
    A webtest record class. It is used to either store a record, or to fetch it from the repository
    """
    _headers_blacklist = set(['set-cookie', 'expires', 'x-varnish', 'x-cache', 'date', 'age', 'last-modified'])
    fuzzy_headers = set(['content-length', 'length'])

    def __init__(self, name, host):
        self.record = name
        self.filepath = os.path.join(testsdir, name)
        self.savepath = os.path.join(savedir, '{}_{}'.format(host, name))
        with open(self.filepath,'r') as fh:
            try:
                self.params = parse(fh.read(), host)
            except:
                print("unable to parse the record %s" % self.filepath)
                raise

    def _fetch(self):
        try:
            r = requests.request(
                self.params.method,
                self.params.url,
                headers = self.params.headers,
                data = self.params.body,
                cookies = self.params.cookies,
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
