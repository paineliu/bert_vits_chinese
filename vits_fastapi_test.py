from time import sleep
import requests
import json
import os
import hashlib

def http_post(ip, port, path, query):
    url = 'http://%s:%s/%s' % (ip, port, path)
    print(url)
    try:
        headers = {'Content-Type': 'application/json'}
        r = requests.post(url=url, data=query, headers=headers)
        return r.content
    except:
        return ""
    
def test_tts1(ip, port, text):
    
    query_json = {}
    query_json['text'] = text
    ret = http_post(ip, port, 'tts1', json.dumps(query_json))
    md5 = hashlib.md5()
    md5.update(text.encode())
    filename = md5.hexdigest() + '.mp3'

    with open(filename, 'wb') as out_file:
        out_file.write(ret)
    print(filename)
    print()

def test_tts(ip, port, text):
    
    query_json = {}
    query_json['text'] = text
    ret = http_post(ip, port, 'tts', json.dumps(query_json))
    print(ret)


if __name__ == "__main__":
    svr_ip = '202.112.194.54'
    svr_port = '8113'
    
    test_tts(svr_ip, svr_port, '儿子')
    # svr_ip = '127.0.0.1'
    # svr_port = '8113'
    # test_tts1(svr_ip, svr_port, '儿子')
