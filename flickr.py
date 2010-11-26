# -*- coding: utf-8 -*-
import sys
from postutil import PostUtil
import flickrapi
from flickrapi.exceptions import FlickrError
import traceback

class PostFlickrUtil(PostUtil):
    def __init__(self, data_):
        self.service_name = "flickr"
        # 必要な設定を検証
        self.require_config = ["flickr_apikey", "flickr_secret"]
        PostUtil.__init__(self)
        self.post(data_)

    def auth_test(self):
        # testの際には認証用URLを表示して手動で入力することでfrobとtokenを得ることにする
        flickr = flickrapi.FlickrAPI(self.config["flickr_apikey"], self.config["flickr_secret"])
        self.logger.debug("access this url and Press Authorize button to complete authorize:")
        self.logger.debug(flickr.web_login_url(perms='write'))
        frob = raw_input("Input frob string and Press ENTER:")
        token = flickr.get_token(frob)
        return (token, frob)

    def get_error_code(self, e):
        return int(e.message.split(':')[1].replace(' ', ''))

    def post(self, data_):
        """
        外部プロセスから呼び出されるメソッド
        data_はrequire_dataにリストされたキーを持つdictに変換できる文字列
        PostUtil.data_decodeに実装された方式でdictにデコードされる
        """
        self.require_data = ["token", "filepath", "title", "is_public", "email", "nickname"]
        data = self.data_decode(data_)
#        if self.debug or data["token"]: data["token"], data["frob"] = self.auth_test()
        if self.debug: self.logger.debug(data)

        if self.valid or self.debug:
#            flickr = flickrapi.FlickrAPI(self.config["flickr_apikey"], self.config["flickr_secret"], format='etree')
            flickr = flickrapi.FlickrAPI(self.config["flickr_apikey"], self.config["flickr_secret"], format='etree', token=data["token"])

            try:
#                flickr.get_token_part_two((data["token"], data["frob"]))
                self.logger.debug('UPLOAD STAR!')
                response = flickr.upload(filename=data["filepath"], title=data["title"], is_public=data["is_public"])
                self.logger.debug('END UPLOAD!!')

                if response.attrib['stat'] == 'ok':
                    self.succeed()
                    self.logger.debug("post succeed")
                else:
                    self.failed()
                    self.logger.debug("flickr post failed")
                    self.logger.warning(response)
            except FlickrError, e:
                self.failed()
                error_code = self.get_error_code(e)
                tb = traceback.format_exc()
                self.logger.debug(tb)
            except Exception, e:
                self.failed()
                tb = traceback.format_exc()
                self.logger.debug(tb)
                self.logger.warning(e)
        else:
            # 内部エラー。必要なデータが足りていない
            self.failed()
            self.logger.warning("invalid data:"+data)

        print 'end'
