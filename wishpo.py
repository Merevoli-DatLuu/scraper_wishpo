import json
from io import BytesIO

import pytesseract
import requests
from PIL import Image
from requests.structures import CaseInsensitiveDict

OEM_OPTIONS = [3]
PSM_OPTIONS = [6, 7, 8, 10, 13]
NO_IMAGE_EXPORT = False
IMAGE_FILE_NAME = 'sample_image.png'
bsid = None
image_content = None
IDS = [
    "WI001159665167FPL",
    "WI001160138049FPL",
    "WI001041808962FPL",
    "WI001062805710FPL",
    "WI001094619943FPL"
]

def get_captcha():
    global bsid, image_content
    CAPTCHA_URL = 'https://www.wishpost.cn/get-new-captcha'
    r = requests.get(CAPTCHA_URL)
    bsid = r.headers['set-cookie'].split(';')[0].split('=')[1]
    image_content = r.content
    # print(bsid)
    if not NO_IMAGE_EXPORT:
        file = open(IMAGE_FILE_NAME, "wb")
        file.write(r.content)
        file.close()

def get_data(ids, captcha):
    TRACKING_URL = 'https://www.wishpost.cn/api/tracking/search'

    headers = CaseInsensitiveDict()
    headers["cookie"] = f"bsid={bsid}"
    headers["Content-Type"] = "application/json"

    data = json.dumps({
        "ids[]": ids,
        "params_num":len(ids),
        "api_name":"tracking/search",
        "captcha": captcha
    })

    r = requests.post(TRACKING_URL, headers=headers, data=data)
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        # print(r.status_code)
        # print(r.text)
        return None

def solve_captcha(with_training = False):
    found_numbers = {}
    result_number = None
    tessdata = ""
    if with_training:
        tessdata = '--tessdata-dir tessdata '

    if NO_IMAGE_EXPORT:
        image_bytes = BytesIO(image_content)
        image = Image.open(image_bytes)
    else:
        image = Image.open(IMAGE_FILE_NAME)

    for oem_option in OEM_OPTIONS:
        for psm_option in PSM_OPTIONS:
            try:
                custom_config = f'{tessdata}--psm {psm_option} --oem {oem_option} -c tessedit_char_whitelist=0123456789'
                guest_number = pytesseract.image_to_string(image, config=custom_config).strip()
                # print(oem_option, " | ", psm_option, end=" | ")
                # print(guest_number, len(guest_number))

                if len(guest_number) == 4 and guest_number.isdigit():
                    if guest_number not in found_numbers:
                        found_numbers[guest_number] = 1
                    else:
                        found_numbers[guest_number] += 1

            except Exception:
                continue

    max_size = 0
    for k, v in found_numbers.items():
        if v > max_size:
            result_number = k

    # print("Result: ", result_number)
    if result_number:
        return [result_number, max_size]
    else:
        return None

def send_data(code):
    API_URL = 'http://0f59-2402-800-63b8-c3a0-403d-1629-e8-2363.ngrok.io/api/upload'
    files = {'image_file': open('sample_image.png','rb')}
    values = {'code': str(code)}

    r = requests.post(API_URL, files=files, data=values)
    print(r.status_code)

def crawl_data():
    returned_data = None

    while returned_data is None:
        get_captcha()

        captcha_res_1 = solve_captcha(with_training=True)
        captcha_res_2 = solve_captcha()

        while captcha_res_1 is None and captcha_res_2 is None:
            get_captcha()

            captcha_res_1 = solve_captcha(with_training=True)
            captcha_res_2 = solve_captcha()

        if captcha_res_1 and captcha_res_2:
            if captcha_res_1[1] >= captcha_res_2[1]:
                captcha_res = captcha_res_1[0]
            else:
                captcha_res = captcha_res_2[0]
        else:
            if captcha_res_1:
                captcha_res = captcha_res_1[0]
            else:
                captcha_res = captcha_res_2[0]

        returned_data = get_data(IDS, captcha_res)

    return captcha_res
    # print(returned_data)
        

if __name__ == '__main__':
    i = 1

    while True:
        code = crawl_data()
        send_data(code)
        print(i, "|", code)
        i += 1
