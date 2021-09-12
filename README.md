# vaxproxy

### What
This tool is a "proxy" which works with a request to medicare's site, gets your vaccination data and turns it into a [EU-compatible](https://ec.europa.eu/info/live-work-travel-eu/coronavirus-response/safe-covid-19-vaccines-europeans/eu-digital-covid-certificate_en) QR-code

The QR-code can be verified by:
- Using a checker app, with the only modification of adding a public key with keyId: `MThhYmM4OWY1NDk0NmE5ZQ==`
- Using this [vacdec](https://github.com/HQJaTu/vacdec) script, and place cert.pem in the `certs` folder as `31386162633839663534393436613965.pem`

See details below.

### How
The proxy sends a request with your cookies to medicare, and converts the JSON containing your vaccination data into a sign1 cose/cbor message, then compresses and base64s the result (as per the EU specs).

### Obtain a QR Code:

**GIANT RED WARNING**: Doing this sends your temporary myGov authentication token to my server. This is very risky, as I could potentially be doing anything with it, including stealing your identity. However: the code that runs this is right here and deploys from the GitHub action and does nothing nefarious. Also I'm not that kind of person, but you have to trust me. Sorry.

- Log in to myGov in your browser
- Go to the following URL while your browser's network developer tools are open: https://www2.medicareaustralia.gov.au/moaapi/moa-ihs/record/cir/data/1
- Find the request in Network, right click and "Copy as cURL"
- In a terminal, paste the request. Change the URL from "https://www2.medicareaustralia.gov.au..." to "https://medicare.whatsbeef.net/?irn=1" and remove the `Host` header. Also add `--output code.png` on the end, because the proxy responds with an image.

If your IRN on your card is not `1`, modify the `irn` GET parameter on the URL to the number on your card.

e.g.:
```
curl 'https://medicare.whatsbeef.net/?irn=1' \
-X 'GET' \
-H 'Cookie: dtCookie=31$B0F37CA9D84ECBB9DCB81E4E5A5D0C3E|6a7b14714a5dead|1; BIGipServerPO_ISAM_WEB_PROD_18443=1597308426.2888.0000; dtLatC=1; dtCookie=31$B0F37CA9D84ECBB9DCB81E4E5A5D0C3E|6a7b14714a5ddb89|1; dtCookie=31$B0F37CA9D343ECBB9DCB81E4E5A5D0C3E; rxVisitor=1631361015077V5KQLBJ10VMIHSI3DQTV03L4G05GCTD1; dtPC=31$568549026_245h-vRUMWGTFNCCOCLAHUGLDLARAUFUHUBGCE-0e2; _ga_VQXYHKRL4N=GS1.1.1631368389.2.1.1631368550.0; rxvt=1631370350699|1631367601640; dtSa=-; PD-S-MOA-SESSION-ID=MjC4jcaGi9F=:1_2_1_E22RDzyzjseJKi5hAWs4Du0vlZIzGyuq6nkAGm28TuFthtqO|; PD-S-SESSION-ID=1_2_0_do3+8RluKptpieznrKqpxtBgpfqQERMmjFZzXIP7dsUkE+3b; _ga=GA1.1.997885341.1631361017; PD_STATEFUL_82227494-dd62-11e8-b73e-0050568e149d=%2Fmoaapi; PD_STATEFUL_227f26e4-2067-11e9-809f-74fe480659ae=%2Fmoasso; PD_STATEFUL_40e85bf4-6fda-11ea-8c46-0050568e629b=%2Fmoaonline' \
-H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
-H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15' \
-H 'Accept-Language: en-au' \
-H 'Accept-Encoding: gzip, deflate, br' \
-H 'Connection: keep-alive' --output test.png
```

### Verify your QR-code
On iOS:
- Check out https://github.com/wabzqem/CovidCertificate-App-iOS
- Modify the signing settings to use your developer team/signing identity
- Run the app on a device, and scan your QR-code

Using `vacdec`:
- Check out https://github.com/HQJaTu/vacdec and follow instructions in README to install
- Place cert.pem from this repository as `31386162633839663534393436613965.pem` in the vacdec folder
- Run `./vacdec --image-file ./test.png` to see your QR-code information
