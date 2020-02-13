#!flask/bin/python
from flask import Flask, request, abort, redirect, make_response, jsonify
import rconst as const
import requests
from device_detector import DeviceDetector

app = Flask(__name__)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/<tx>', methods=['GET'])
def deeplink(tx):
    if tx.startswith('tx'):
        ua = request.headers.get('User-Agent')
        device = DeviceDetector(ua).parse()
        bot = device.is_bot()
        if not bot:
            dtype = device.device_type()
            data = post(const.local_backend, "SELECT tx_sp FROM txs WHERE tx='" + str(tx) + "'")
            if dtype == 'smartphone':
                return redirect('minter://' + data, code=302)
            elif dtype == 'desktop':
                return redirect('https://bip.to/' + data, code=302)
            else:
                abort(403)
        else:
            abort(403)
    else:
        abort(404)


@app.route('/sql', methods=['POST'])
def sql():
    addr = request.remote_addr
    args = request.args
    if addr == const.local_frontend:
        post(const.local_backend)
    elif args['local'] == 'yes':
        post(const.local_backend)
    else:
        abort(403)


def post(ip):
    r = requests.post('http://' + ip + ':5000/sql')
    if r.status_code == 200:
        return 'abbbc'
    else:
        abort(500)


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
