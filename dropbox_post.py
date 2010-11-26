# -*- coding: utf-8 -*-
import sys, os
from postutil import PostUtil
try:
    from dropbox import client, auth, rest
except ImportError, e:
    print(sys.path)
import traceback

class PostDropboxUtil(PostUtil):
    def __init__(self, data_):
        self.service_name = "dropbox"
        self.require_config = ["dropbox_apikey", "dropbox_secret"]
        PostUtil.__init__(self)
        self.dropbox_config = {
            'server': 'api.dropbox.com',
            'content_server': 'api-content.dropbox.com',
            'port':  80,
            'consumer_key': self.config["dropbox_apikey"],
            'consumer_secret': self.config["dropbox_secret"],
            'verifier': '',
            'request_token_url': 'https://api.dropbox.com/0/oauth/request_token',
            'access_token_url': 'https://api.dropbox.com/0/oauth/access_token',
            'authorization_url': 'https://www.dropbox.com/0/oauth/authorize',
            'trusted_access_token_url': 'https://api.dropbox.com/0/token',
        }
        self.post(data_)


    def login_and_authorize(self, authorize_url):
        from mechanize import Browser, FormNotFoundError
        import getpass
        print "AUTHORIZING", authorize_url
        br = Browser()
        br.set_debug_redirects(True)
        br.open(authorize_url)
        print "FIRST PAGE", br.title(), br.geturl()
        br.select_form(nr=1)
        br['login_email'] = raw_input('Enter your dropbox email: ')
        br['login_password'] = getpass.getpass('Enter your dropbox password: ')
        resp = br.submit()
        print "RESULT PAGE TITLE", br.title()
        print "RESULT URL", resp.geturl()
        assert br.viewing_html(), "Looks like it busted."
        try:
            br.select_form(nr=1)
            br.submit()
            assert br.viewing_html(), "Looks like it busted."
            assert "API Request Authorized" in br.title(), "Title Is Wrong (bad email/password?): %r at %r" % (br.title(), br.geturl())
        except FormNotFoundError:
            print "Looks like we're blessed."

    def auth_test(self):
        dba = auth.Authenticator(self.dropbox_config)
        req_token = dba.obtain_request_token()
        assert req_token and dba.oauth_request
        authorize_url = dba.build_authorize_url(req_token)
        self.login_and_authorize(authorize_url)
        access_token = dba.obtain_access_token(req_token, self.dropbox_config['verifier'])
        assert access_token
        assert dba.oauth_request
        assert access_token.key != req_token.key
        return access_token

    def get_client(self, token):
        config = self.dropbox_config
        author = auth.Authenticator(config)
        return client.DropboxClient(config['server'], config['content_server'], config['port'], author, token)

    def logging(self, resp):
        self.logger.debug(resp.status)
        self.logger.debug(resp.headers)
        self.logger.debug(resp.body)

    def post(self, data_):
        self.require_data = ["token", "filepath", "filename", "dirname" "email", "nickname"]
        data = self.data_decode(data_)
        if self.debug:
            data["token"] = self.auth_test()
            self.logger.debug(data)
        folder_path = data['dirname'] # slash必須

        if self.valid or self.debug:
            dropbox = self.get_client(data["token"])
            file_obj = file(data["filepath"])
            try:
                # file 配置
                resp = dropbox.put_file("dropbox", folder_path, file_obj)
                if self.debug: self.logging(resp)
                # file 移動
                from_path = folder_path + os.path.basename(data["filepath"])
                to_path = folder_path + data["filename"]
                resp = dropbox.file_move("dropbox", from_path, to_path)
                if self.debug: self.logging(resp)
                if resp.status == 200:
                    self.succeed()
                    self.logger.debug("post succeed")
                else:
                    self.failed()
                    self.logging(resp)
            except Exception, e:
                self.failed()
                tb = traceback.format_exc()
                self.logger.debug(tb)
                self.logger.warning(e)
        else:
            self.failed()
            self.logger.warning("invalid data:"+data)

