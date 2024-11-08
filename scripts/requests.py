import urllib.parse
import subprocess
import json

class Request:
    def __init__(self, method='GET', url=None):
        self.method = method
        self.url = url
        self.params = {}
        self._data = None
        self.headers = {}

    def params(self, params):
        if isinstance(params, dict) and 'json' in params:
            self.params = json.dumps(params['json'])
        else:
            self.params = params
        return self

    def data(self, data):
        if isinstance(data, dict) and 'json' in data:
            self._data = json.dumps(data['json'])
        elif isinstance(data, str) and data.startswith('{') and data.endswith('}'):
            self._data = data
        else:
            self._data = urllib.parse.urlencode(data)
        return self

    def header(self, key, value):
        self.headers[key] = value
        return self

class Session:
    def __init__(self):
        self.base_url = ''

    def get(self, url, **kwargs):
        req = Request('GET', url)
        for k, v in kwargs.items():
            if isinstance(v, dict) and 'params' in v:
                req.params(**v['params'])
            elif k == 'headers':
                for header_key, header_value in v.items():
                    req.header(header_key, header_value)
        return req

    def post(self, url, **kwargs):
        req = Request('POST', url)
        print(kwargs)
        for k, v in kwargs.items():
            if isinstance(v, dict) and 'json' in v:
                req.data(**v['data'])
            elif k == 'headers':
                for header_key, header_value in v.items():
                    req.header(header_key, header_value)
        return req

    def send(self, req):
        url = req.url
        method = req.method
        params = req.params if isinstance(req.params, dict) else {}
        headers = req.headers if isinstance(req.headers, dict) else {}
        data = req.data if isinstance(req.data, str) and req.data.startswith('{') and req.data.endswith('}') else None

        command = ['curl', '-X', method]
        for key, value in headers.items():
            command.append('-H')
            command.append(f'{key}: {value}')
        if method == 'POST':
            if data:
                command.extend(['-d', data])
            else:
                command.append('-d')
                command.append('empty body')
        elif method == 'GET':
            for key, value in params.items():
                command.append(f'--data-urlencode')
                command.append(f'{key}={value}')

        command.append(url)

        try:
            response = subprocess.check_output(command)
            print(response)
            import pdb; pdb.set_trace()
            return Response(json.loads(response))
        except Exception as e:
            raise e

session = Session()

def get(url, params=None, headers=None):
    if not url.startswith('http'):
        raise ValueError("URL must start with 'http' or 'https'")
    req = session.get(url).params(params or {})
    if headers:
        for key, value in headers.items():
            req.header(key, value)
    return session.send(req)

def post(url, json=None, headers=None):
    if not url.startswith('http'):
        raise ValueError("URL must start with 'http' or 'https'")
    req = session.post(url, json=json).data(json or {})
    if headers:
        for key, value in headers.items():
            req.header(key, value)
    return session.send(req)

class Response:
    def __init__(self, body, headers=None):
        self.body = body
        self.status_code = 200
        self.headers = headers

    def json(self):
        try:
            return json.loads(self.body)
        except ValueError:
            raise ValueError('Invalid JSON')
