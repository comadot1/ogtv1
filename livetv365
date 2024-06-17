from flask import Flask, render_template, request, Response
from werkzeug.utils import secure_filename
from werkzeug.serving import WSGIRequestHandler
import logging
import time
import requests
import json
from datetime import datetime
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import re
from urllib.parse import urlparse

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

livetvUrl = 'https://speed10.net/player/player.php?co=01&ch='

headers = {'sec-Fetch-Mode': 'no-cors',
           'sec-Fetch-Site': 'cross-site',
           'sec-Fetch-Dest': 'empty',
           'sec-ch-ua-platform': '"Windows"',
           'Pragma': '"no-cache"',
           'accept': '*/*',
           'Referer': 'https://xn--oi2bm8j2eu57aboo.com',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
           'Origin': 'https://xn--oi2bm8j2eu57aboo.com',
           'sec-ch-ua-mobile': '?0',
           'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"'
           }

headers_img = {'sec-Fetch-Mode': 'no-cors',
           'sec-Fetch-Site': 'cross-site',
           'sec-Fetch-Dest': 'image',
           'sec-ch-ua-platform': '"Windows"',
           'Pragma': '"no-cache"',
           'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
           'Host': 'www.memetv1.com',
           'Referer': 'https://xn--oi2bm8j2eu57aboo.com/',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
           'Origin': 'https://xn--oi2bm8j2eu57aboo.com',
           'sec-ch-ua-mobile': '?0',
           'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"'
           }

channel_select = ""
phpurl_cnt_init = 1


@app.route('/playlist.m3u8', methods=['GET', 'POST'])
def get_playlist():
    temp = request.args.get('chval', "1")
    channel_select = temp
    chunkUrl = ''

    try:
        globals()[f"phpurl_{channel_select}"]
    except:
        globals()[f"phpurl_{channel_select}"] = ''

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
        global phpurl_cnt_init

        # 라이브티비 채널 php 를 불러와서 playlist m3u8 따기, 라이브채널 php를 매번 호출하면 차단 당할 위험
        phpurl_cnt_init += 1
        if phpurl_cnt_init > 1000:
            phpurl_cnt_init = 0
            globals()[f"phpurl_{channel_select}"] = '';
        else:
            print('뭐야')

        if globals()[f"phpurl_{channel_select}"] == '':
            print('갱신필요')

            url = livetvUrl + channel_select
            globals()[f"phpurl_{channel_select}"] = url

            retryCnt = 0

            while retryCnt < 6:
                retryCnt += 1
                my_session = create_session()
                headers['Host'] = None
                response = send_request(my_session, globals()[f"phpurl_{channel_select}"], 'GET', None, None,
                                        headers=headers)

                if response.status_code == 200:
                    html_content = response.text
                    # print(response.text)
                    matches = re.findall(r'https://\S+', response.text)
                    # playlist.m3u8 구하기
                    print(matches)
                    m3u8_links = [link for link in matches if re.search(r'm3u8', link)]
                    print(m3u8_links)
                    playlistDataUrl = m3u8_links[0][:-2]
                    globals()[f"playlistDataUrl_{channel_select}"] = playlistDataUrl
                    print('playlistDataUrl:', playlistDataUrl[0][:-2])

                    parsed_url = urlparse(playlistDataUrl)
                    # 도메인 출력
                    domain = parsed_url.netloc
                    headers['Host'] = domain
                    headers_img['Host'] = domain
                    print(headers)

                    #image_url = f"https://{domain}/liveedge/live{channel_select}/image.gif"
                    # image_url = matches[5].split("'")[0]
                    image_url = [link for link in matches if re.search(r'gif', link)]
                    print(image_url)

                    response2 = send_request(my_session, image_url[0][:-1], 'GET', None, None, headers=headers_img)

                    print(response2.status_code)
                    time.sleep(0.5)

                    response = send_request(my_session, playlistDataUrl, 'GET', None, None,headers=headers)

                    if response.status_code == 200:
                        print("Success! Status code: 200")
                        lines = response.text.split('\n')
                        # chunk m3u8 주소 구하기(실제 재생할 ts 파일의 주소를 얻기 위함)
                        chunkUrl = playlistDataUrl.split('playlist')[0] + lines[3]

                        if chunkUrl == '':
                            print('if:', chunkUrl)
                        else:
                            globals()[f"chunkUrl_{channel_select}"] = chunkUrl
                            print('else:', chunkUrl)
                            break
                    else:
                        print(f"playlist Retrying... Status code: {response.status_code}")
                        # 일정 시간 동안 대기하고 다시 시도할 수 있도록 sleep 추가
                        # time.sleep(0.1)
                else:
                    print(f"Failed to retrieve data. Status code: {response.status_code}")

            if retryCnt == 5:
                globals()[f"phpurl_{channel_select}"] = ''

        else:
            print(phpurl_cnt_init, '유지 중')

        try:
            globals()[f"chunkUrl_{channel_select}"]
        except:
            globals()[f"chunkUrl_{channel_select}"] = ''

        if globals()[f"chunkUrl_{channel_select}"] == '':
            globals()[f"phpurl_{channel_select}"] = ''

        return get_chunk_data(globals()[f"chunkUrl_{channel_select}"], channel_select)
    else:
        return ""


def get_chunk_data(chunk_url, channel_select):
    # print('get_chunk_data:', chunk_url)
    segments = chunk_url.split('/')
    extracted_string = '/'.join(segments[:5])

    # chunk m3u8 를 호출하여 실제 ts파일 주소를 추출
    sess = get_session()

    res = sess.get(globals()[f"chunkUrl_{channel_select}"], headers=headers)

    if res.status_code == 200:
        ts_text = inplace_linechange(extracted_string, res.content,
                                     old_string='EXT-X-TARGETDURATION',
                                     new_string=f'#EXT-X-TARGETDURATION:2')
    else:
        ts_text = "none"
        print(f"chunk Retrying... Status code: {res.status_code}")
        globals()[f"phpurl_{channel_select}"] = ''

    # 실제 ts 주소
    # print(ts_text)

    res.close()

    response = Response(
        ts_text,
        status=200,
        # mimetype="text/csv",
        content_type='application/vnd.apple.mpegurl',
    )
    response.headers["Connection"] = "keep-alive"

    return response


def create_session():
    session = requests.Session()
    return session


def send_request(session, url, method='GET', params=None, data=None, headers=None):
    try:
        if method == 'GET':
            response = session.get(url, params=params, headers=headers)
        elif method == 'POST':
            response = session.post(url, params=params, data=data, headers=headers)
        else:
            # 다른 HTTP 메서드에 대한 처리도 추가 가능
            raise ValueError("지원되지 않는 HTTP 메서드입니다.")

        response.raise_for_status()  # 오류가 발생하면 예외 발생
        return response
    except requests.exceptions.RequestException as e:
        print(f"오류 발생: {e}")
        return None


def inplace_linechange(chval, filename, old_string, new_string):
    lines = filename.decode('utf-8').strip()
    lines2 = lines.split("\n")
    '''
    for i, line in enumerate(lines2):
        if line.startswith("#EXT-X-TARGET"):
            lines2[i] = "#EXT-X-TARGETDURATION:2"
    '''
    lines = "\n".join(lines2)
    new_txt = lines.replace('media_', f'{chval}/media_')

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
