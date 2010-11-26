# -*- coding: utf-8 -*-
from flask.config import Config
from flaskext.mailutils import sendmail
import logging
import traceback
import pickle

class PostUtil:
    valid = True
    require_config = []
    require_data = []
    def __init__(self, debug=False):
        self.valid = True
        # loggerを初期化する
        logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
        logger = logging.getLogger(self.service_name)
        logger.setLevel(logging.DEBUG)
        self.logger = logger
        # 設定ファイルからAPIkeyとかを読み込む
        current_dir = os.path.dirname(__file__)
        config = Config('../../')
        if os.path.exists(activate_this):
            config.from_pyfile("wsgi_dev.cfg")
        else:
            config.from_pyfile("dev.cfg")
        #self.logger.debug(config)
        self.validate(self.require_config, config['EXTERNAL_CONFIG'])
        self.config = config['EXTERNAL_CONFIG']
        self.debug = config['POST_DEBUG']

    def validate(self, list_, dict_):
        for key in list_:
            if not key in dict_:
                self.logger.warning("undefined "+key)
                self.valid = False

    def data_decode(self, data_):
        try:
            data = pickle.loads(data_)
            self.validate(self.require_data, data)
            self.email = data['email']
            self.nickname = data['nickname']
            return data
        except pickle.PicklingError, e:
            self.logger.warning(e)
            self.valid = False

    def post(self, data_):
        pass

    def succeed(self):
        try:
            mail_template_path = "main/mail/post_succeed.txt"
            sendmail(self.email, mail_template_path, dict(self.nickname, self.service_name))
        except Exception, e:
            tb = traceback.format_exc()
            self.logger.debug(tb)
            self.logger.debug(e)

    def failed(self):
        try:
            mail_template_path = "main/mail/post_failed.txt"
            sendmail(self.email, mail_template_path, dict(self.nickname, self.service_name))
        except:
            tb = traceback.format_exc()
            self.logger.debug(tb)
            self.logger.debug(e)
