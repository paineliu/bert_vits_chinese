from time import sleep
import requests
import json
import os
import hashlib

def http_post(ip, port, path, query):
    url = 'http://%s:%s/%s' % (ip, port, path)
    print(url)
    try:
        r = requests.post(url=url, data=query)
        return r.content
    except:
        return ""
    
def test_tts(ip, port, text):
    
    query_json = {}
    query_json['text'] = text
    ret = http_post(ip, port, 'tts', json.dumps(query_json))
    md5 = hashlib.md5()
    md5.update(text.encode())
    filename = md5.hexdigest() + '.mp3'

    with open(filename, 'wb') as out_file:
        out_file.write(ret)
    print(filename)
    print()


if __name__ == "__main__":
    svr_ip = '202.112.194.54'
    svr_port = '8113'
    
    test_tts(svr_ip, svr_port, '苹果能吃吗？可以吃！')
