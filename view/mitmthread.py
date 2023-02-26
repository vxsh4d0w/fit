import ssl
import sys
import asyncio
from datetime import datetime

import certifi
import mitmproxy.http
import warcio
from PyQt5.QtCore import QUrl, QObject, pyqtSignal, QThread
import logging

from PyQt5.QtNetwork import QNetworkProxy, QSslCertificate, QSslConfiguration
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication
from mitmproxy import utils, http
from mitmproxy.tools import main
from mitmproxy.tools.dump import DumpMaster
from warcio import StatusAndHeaders
from warcio.warcwriter import WARCWriter


class ProxyServer(QObject):

    logging.basicConfig(filename='mitmproxy.log', level=logging.INFO)
    proxy_started = pyqtSignal(int)

    def __init__(self, port):
        super().__init__()
        self.port = port

    async def start(self):
        # set proxy opts
        options = main.options.Options(listen_host='127.0.0.1', listen_port=self.port,
                                       ssl_insecure=True)
        master = DumpMaster(options=options)

        # addons in mitmproxy are used to provide additional features and customize proxy's behavior
        # this way, we can create custom addons to intercept everything and create the warc/wacz files

        master.addons.add(FlowReaderAddon())

        try:
            await master.run()
        except KeyboardInterrupt:
            master.shutdown()

# creating a custom addon to save flow as warc
def FlowToWarc(flow: http.HTTPFlow):
    warc_file = 'test_warc.warc'
    with open(warc_file, 'ab') as output:

        # create new warcio writer
        writer = WARCWriter(output, gzip=False)
        content_type = flow.response.headers.get('content-type', '').split(';')[0]
        payload = flow.response.content

        headers = flow.response.headers.items()

        date_obj = datetime.fromtimestamp(flow.response.timestamp_start)
        # Convert the datetime object to an ISO formatted string
        iso_date_str = date_obj.isoformat()
        '''
        headers= []
        for name, value in flow.response.headers.items():
        headers.append((name.lower(), value))'''
        http_headers = StatusAndHeaders(str(flow.response.status_code) + ' ' + flow.response.reason, headers,
                                        protocol=flow.response.http_version)

        warc_headers = {
            'WARC-Type': 'response',
            'WARC-Target-URI': flow.request.url,
            'WARC-Date': iso_date_str,
            'Content-Type': content_type,
            'Content-Length': str(len(payload)),
        }
        record = writer.create_warc_record(flow.request.url, 'response',
                                           payload=payload,
                                           http_headers=http_headers,
                                           warc_headers_dict=warc_headers)
        print(record)
        writer.write_record(record)


# creating a custom addon to intercept requests and reponses, printing url, status code, headers and content
class FlowReaderAddon:
    def request(self, flow: mitmproxy.http.HTTPFlow):

        pass
        '''print("Request URL: " + flow.request.url)
        print("Request Headers: " + str(flow.request.headers))
        print("Request Content: " + str(flow.request.content))'''

    def response(self, flow: mitmproxy.http.HTTPFlow):
        FlowToWarc(flow)
        pass
        '''print("Response Status Code: " + str(flow.response.status_code))
        print("Response Headers: " + str(flow.response.headers))
        print("Response Content: " + str(flow.response.content))'''

# the proxy needs to be started on a different thread
class MitmThread(QThread):
    def __init__(self, port):
        super().__init__()
        self.port = port

    def run(self):
        # create new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # mitmproxy's creation
        proxy_server = ProxyServer(self.port)
        asyncio.get_event_loop().run_until_complete(proxy_server.start())


class MainWindow(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)

        der_data = set_ssl_config()
        pem_data = ssl.DER_cert_to_PEM_cert(der_data)
        self.page().profile().setHttpUserAgent(pem_data)

        # set port and start the thread (while creating the mainwindow)
        port = 8081
        self.mitm_thread = MitmThread(port)
        self.mitm_thread.start()

        url = QUrl("https://www.google.com/")
        super().load(url)


def set_ssl_config():
    # get the pem with openssl from the mitmproxy .p12
    # openssl pkcs12 -in {mitmproxy-ca-cert.p12} -out {cert_pem} -nodes

    # add pem to the trusted root certificates (won't solve the problem)
    cert_file_path = certifi.where()
    pem_path= 'C:\\Users\\Routi\\Downloads\\mitmproxy-ca-cert.pem'
    with open(pem_path, 'rb') as pem_file:
        pem_data = pem_file.read()
    with open(cert_file_path, 'ab') as cert_file:
        cert_file.write(pem_data)

    # create a QSslConfiguration object with the certificate as the CA certificate (won't solve the problem neither)
    cert = QSslCertificate(pem_data)
    config = QSslConfiguration.defaultConfiguration()
    config.setCaCertificates([cert])

    # get the DER-encoded certificate data
    der_data = cert.toDer()
    return der_data


if __name__ == "__main__":
    app = QApplication(sys.argv)

    webview = MainWindow()
    # create the proxy
    proxy = QNetworkProxy(QNetworkProxy.HttpProxy, '127.0.0.1', 8081)
    QNetworkProxy.setApplicationProxy(proxy)

    webview.show()
    sys.exit(app.exec_())
