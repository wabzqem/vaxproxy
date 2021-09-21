from io import BytesIO
import cbor2
from cose.algorithms import Es256
from cose.headers import Algorithm, KID
from cose.keys.keyparam import EC2KP, EC2KpCurve, EC2KpD, EC2KpX, EC2KpY, KpKeyOps, KpKty
from cose.keys.keytype import KtyEC2
from cose.messages import Sign1Message
from cose.keys import CoseKey, keyops, curves

from binascii import unhexlify, hexlify
from pprint import pprint

import zlib
import base45
import qrcode
import json
import requests
from urllib.request import urlopen
from pikepdf import Pdf

import time
import datetime
from os import getenv

from flask import Flask, request, make_response, send_file, jsonify
app = Flask(__name__)

priv_key = {
    KpKty: KtyEC2,
    EC2KpCurve: curves.P256,
    KpKeyOps: [keyops.SignOp, keyops.VerifyOp],
    EC2KpX: unhexlify(b'fa5e3ee7ccf4b52056fba3f275a3c3a8867c9ffcccfac20f59e9db49bfccf26e'),
    EC2KpY: unhexlify(b'6b278200cd45d22127525e9c7272b67b722f029e40ec55547886a1ae0ffde966'),
    EC2KpD: unhexlify(getenv("CERT_PRIVKEY"))
}

@app.route('/pdf')
def pdf():
    irn = request.args.get('irn')
    resp = requests.request(
        method=request.method,
        url="https://www2.medicareaustralia.gov.au/moaapi/moa-ihs/record/covid/view/{}".format(irn),
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

    pdf = Pdf.open(BytesIO(resp.content))
    return serve_pdf(pdf)

@app.route('/')
def create_image():
    irn = request.args.get('irn')
    resp = requests.request(
        method=request.method,
        url="https://www2.medicareaustralia.gov.au/moaapi/moa-ihs/record/cir/data/{}".format(irn),
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)    
    json_data = json.loads(resp.content.decode("utf-8"))

    if ("errorList" in json_data): # Probably "immunisation record not up to date"
        return make_response(jsonify(json_data), 404)

    validTo = datetime.datetime.strptime(json_data['immunisationRecordData']['immunisationRecordMetadata']['dateValidTo'], '%Y-%m-%d')
    dateGenerated = datetime.datetime.strptime(json_data['immunisationRecordData']['immunisationRecordMetadata']['dateGenerated'][:10], '%Y-%m-%d')
    out_obj = {
        1: "AU",
        4: int(time.mktime(validTo.timetuple())),
        6: int(time.mktime(dateGenerated.timetuple())),
        -260: {
            1: {
                "dob": json_data['immunisationRecordData']['individualDetails']['dateOfBirth'],
                "nam": {
                    "fn": json_data['immunisationRecordData']['individualDetails']['lastName'],
                    "gn": "{} {}".format(json_data['immunisationRecordData']['individualDetails']['firstName'], json_data['immunisationRecordData']['individualDetails']['initial']).strip(),
                    "fnt": json_data['immunisationRecordData']['individualDetails']['lastName'].upper(),
                    "gnt": "{} {}".format(json_data['immunisationRecordData']['individualDetails']['firstName'], json_data['immunisationRecordData']['individualDetails']['initial']).strip().upper()
                },
                "ver": "1.3.0"
            },
        }
    }
    out_obj[-260][1]["v"] = []
    v = json_data['immunisationRecordData']['immunisationStatus']['vaccineInfo'][-1]
    entry = {
        "tg": "840539006", # COVID-19
        "co": "AU", # State where administered
        "is": "Australian Department of Health", # Certificate issuer
        "ci": "URN:UVCI:{}".format(json_data['immunisationRecordData']['immunisationRecordMetadata']['immunisationRecordId'])
    }

    if (v['vaccineBrand'] == 'Pfizer Comirnaty'):
        entry["vp"] = "1119349007" # a SARS-CoV-2 mRNA vaccine
        entry["mp"] = "EU/1/20/1528" # Comirnaty
        entry["ma"] = "ORG-100030215" # Biontech Manufacturing GmbH (is this what we get?)
    elif 'Astra' in v['vaccineBrand']:
        entry["vp"] = "1119305005" # a SARS-CoV-2 antigen vaccine
        entry["mp"] = "EU/1/21/1529" # Vaxzevria
        entry["ma"] = "ORG-100001699" # AstraZeneca
    
    entry["dn"] = 2 # number in series of doses
    entry["sd"] = 2 # overall number in series
    entry["dt"] = v['immunisationDate']
    out_obj[-260][1]["v"].append(entry)
        
    pay = cbor2.dumps(out_obj)
    msg = Sign1Message(phdr = {Algorithm: Es256, KID: b'18abc89f54946a9e'}, payload = pay)
    cose_key = CoseKey.from_dict(priv_key)
    msg.key = cose_key
    encoded = msg.encode()
    compressed = zlib.compress(encoded)
    string = "HC1:{}".format(base45.b45encode(compressed).decode())
    return serve_image(qrcode.make(string))

def serve_image(pil_img):
    img_io = BytesIO()
    pil_img.save(img_io)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

def serve_pdf(pdf):
    pdf_io = BytesIO()
    pdf.save(pdf_io)
    pdf_io.seek(0)
    return send_file(pdf_io, mimetype='application/pdf')

if __name__ == "__main__":
    print("RUNNING")
    app.run(host='0.0.0.0', port=5000)
