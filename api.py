import os

from flask import Flask
from flask_restful import reqparse, abort, Api, Resource

from gpapi.googleplay import (
    GooglePlayAPI, LoginError, RequestError, SecurityCheckError
)

from dotenv import load_dotenv

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('package_name', type=str, help='Bundle id of the apk')

load_dotenv()
GSFID = os.getenv('GSFID')
TOKEN = os.getenv('AUTH_SUB_TOKEN')
LOCALE = os.getenv('LOCALE')
TIMEZONE = os.getenv('TIMEZONE')
DEVICE_CODENAME = os.getenv('DEVICE_CODENAME')

gplayapi = GooglePlayAPI(
    locale=LOCALE,
    timezone=TIMEZONE,
    device_codename=DEVICE_CODENAME
)

gplayapi.login(gsfId=int(GSFID), authSubToken=TOKEN)


class Download(Resource):
    def post(self):
        args = parser.parse_args()
        package_name = args.get('package_name')
        if package_name is None:
            abort(404, message="package_name is required")
        try:
            detail = gplayapi.details(package_name)
        except RequestError as exc:
            abort(404, message=exc.value)
        try:
            if detail['offer'][0]['checkoutFlowRequired']:
                method = gplayapi.delivery
            else:
                method = gplayapi.download
            data_iter = method('nic.goi.aarogyasetu')
            with open('a.apk', 'w+') as temp:
                for index, chunk in enumerate(data_iter['file']['data']):
                    temp.write(chunk)
        except IndexError:
            msg = "Package does not exist {}".format('bundle_id')
            abort(404, message=msg)
        except Exception as exc:
            msg = "Error while downloading {} : {}".format('bundle_id', exc)
            abort(404, message=msg)


api.add_resource(Download, '/download')

if __name__ == '__main__':
    app.run(debug=True)
