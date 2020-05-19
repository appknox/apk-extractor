import os

from flask import Flask, send_file
from flask_restful import reqparse, abort, Api, Resource

from gpapi.googleplay import (
    GooglePlayAPI, LoginError, RequestError, SecurityCheckError
)

from dotenv import load_dotenv

from device_map import device_conf


app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('package_name', type=str, help='Bundle id of the apk')
parser.add_argument('timezone', type=str, help='Timezone')
parser.add_argument('platform', type=str, help='Platform')


load_dotenv()
GSFID = os.getenv('GSFID')
TOKEN = os.getenv('AUTH_SUB_TOKEN')
LOCALE = os.getenv('LOCALE')
TIMEZONE = os.getenv('TIMEZONE')
DEVICE_CODENAME = os.getenv('DEVICE_CODENAME')


def get_api_client(gsfId, token, timezone, device_codename):
    gplayapi = GooglePlayAPI(
        locale=LOCALE,
        timezone=timezone,
        device_codename=device_codename
    )
    gplayapi.login(gsfId=int(gsfId), authSubToken=token)
    return gplayapi


def get_device_codename(platform, timezone):
    for conf in device_conf:
        platforms = conf.get('platforms')
        ctimezone = conf.get('timezone')
        if platform in platforms and timezone == ctimezone:
            return conf.get('device_codename')
    return 'bacon'


class Download(Resource):
    def post(self):
        args = parser.parse_args()
        package_name = args.get('package_name')
        if package_name is None:
            abort(404, message="package_name is required")
        timezone = args.get('timezone')
        platform = args.get('platform')
        print(timezone, platform)
        device_codename = get_device_codename(platform, timezone)
        print(device_codename)
        try:
            print(GSFID, TOKEN)
            gplayapi = get_api_client(GSFID, TOKEN, timezone, device_codename)
        except Exception as exc:
            abort(404, message=exc.value)
        try:
            detail = gplayapi.details(package_name)
        except RequestError as exc:
            abort(404, message=exc.value)
        try:
            if detail['offer'][0]['checkoutFlowRequired']:
                method = gplayapi.delivery
            else:
                method = gplayapi.download
            data_iter = method(package_name)
            with open('a.apk', 'w+') as temp:
                for index, chunk in enumerate(data_iter['file']['data']):
                    temp.write(chunk)
        except IndexError:
            msg = "Package does not exist {}".format('bundle_id')
            abort(404, message=msg)
        except Exception as exc:
            msg = "Error while downloading {} : {}".format(package_name, exc)
            abort(404, message=msg)


api.add_resource(Download, '/download')

if __name__ == '__main__':
    app.run(debug=True)
