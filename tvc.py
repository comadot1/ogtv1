import json
import logging
import time
from datetime import datetime

import requests
from flask import Flask, Response, render_template, request
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from werkzeug.serving import WSGIRequestHandler
from werkzeug.utils import secure_filename

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)


streamUrl = 'https://azure2986.fastedge.net/live/'

headers = {'sec-Fetch-Mode': 'cors',
           'sec-Fetch-Dest': 'empty',
           'Host': 'azure2986.fastedge.net',
           'sec-ch-ua-platform': '"Windows"',
           'sec-ch-ua-mobile': '?0',
           'scheme': 'https',
           'accept': '*/*',
           'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
           'Referer': 'https://sdr4w5g.allyearcdn.com/',
           'method': 'GET',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
           'Origin': 'https://sdr4w5g.allyearcdn.com',
           'authority': 'azure2986.fastedge.net',
           'Accept-Encoding': 'gzip, deflate, br',
           'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
           }

# 파일 다운로드 처리
@app.route('/m3uGet.m3u8', methods=['GET', 'POST'])
def down_file():
    temp = request.args.get('chval', "4ofux18f5c")
    if request.method == 'POST':
        return "error"
    if request.method == 'HEAD':
        response = Response(
            None,
            status=200,
            # mimetype="text/csv",
            content_type='application/vnd.apple.mpegurl',
        )

        response.headers["Content-Disposition"] = "attachment; filename="f'{temp}.m3u8'  # 다운받았을때의 파일 이름 지정해주기
        response.headers["Connection"] = "keep-alive"

        return response
    if request.method == 'GET':
        param = temp

        url = f'{streamUrl}{param}/chunklist.m3u8'
        # res = requests.get(url, headers=headers)

        sess = get_session()
        res = sess.get(url, headers=headers)

        m3u8_text = inplace_linechange(temp, res.content,
                                       old_string='EXT-X-TARGETDURATION',
                                       new_string=f'#EXT-X-TARGETDURATION:2')

        res.close()

        now = time
        # print(now.strftime('%Y-%m-%d %H:%M:%S'), f'\n{m3u8_text}')

        response = Response(
            m3u8_text,
            status=200,
            # mimetype="text/csv",
            content_type='application/vnd.apple.mpegurl',
        )

        response.headers["Content-Disposition"] = "attachment; filename="f'{temp}.m3u8'  # 다운받았을때의 파일 이름 지정해주기
        response.headers["Connection"] = "keep-alive"

        return response


@app.route('/<path>/<filename>', methods=['GET', 'POST'])
def down_ts(path, filename):
    if request.method == 'POST':
        return "error"
    if request.method == 'GET':
        url = f'{streamUrl}{path}/{filename}'
        # res = requests.get(url, headers=headers)
        sess = get_session()
        res = sess.get(url, headers=headers)

        response = Response(
            res.content,
            status=200,
            # mimetype="text/csv",
            content_type='video/MP2T',
        )
        response.headers["Connection"] = "keep-alive"

        res.close()

    return response


def inplace_linechange(chval, filename, old_string, new_string):
    lines = filename.decode('utf-8').strip()

    lines2 = lines.split("\n")
    for i, line in enumerate(lines2):
        if line.startswith("#EXT-X-TARGET"):
            lines2[i] = "#EXT-X-TARGETDURATION:2"
    lines = "\n".join(lines2)
    new_txt = lines.replace('media-', f'{chval}/media-')
    return new_txt

def get_session(
    retries=1, # 재시도 횟수
    backoff_factor=0.1, # 재시도 간격, 곱으로 증가
    status_forcelist=(500, 502, 504), # 무시할 Status 코드
    session=None
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session

if __name__ == '__main__':
    # 서버 실행
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    app.run(host='0.0.0.0', port=7777, debug=False)


