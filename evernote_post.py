# -*- coding: utf-8 -*-
import sys
import hashlib
import time
from postutil import PostUtil
import oauthlib as oauth
import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types
import traceback

class PostEvernoteUtil(PostUtil):
    def __init__(self, data_):
        self.service_name = "evernote"
        self.require_config = ["evernote_apikey", "evernote_secret"]
        PostUtil.__init__(self)
        self.post(data_)

    def auth_test(self):
        import httplib
        # testの際には認証用URLを表示して手動で入力することでtokenを得ることにする
        connection = httplib.HTTPSConnection("www.evernote.com")
        consumer = oauth.OAuthConsumer(self.config["evernote_apikey"], self.config["evernote_secret"])
        sign_method = oauth.OAuthSignatureMethod_PLAINTEXT()

        # 認証なしのtokenを得る get_unauthorised_request_token
        params={'oauth_callback':'http://localhost/callback'}
        oauth_req = oauth.OAuthRequest.from_consumer_and_token(
          consumer, http_url="https://www.evernote.com/oauth", parameters=params )
        oauth_req.sign_request(sign_method, consumer, None)
        url = oauth_req.to_url()
        self.logger.debug(url)
        connection.request(oauth_req.http_method, url)
        resp = connection.getresponse().read()
        self.logger.debug(resp)
        tmp_token = oauth.OAuthToken.from_string(resp)
        tmp_token.to_string()

        # token を認証するためのURLを得る get_authorisation_url
        oauth_req = oauth.OAuthRequest.from_consumer_and_token(
            consumer, token=tmp_token, http_url="https://www.evernote.com/OAuth.action", parameters=params )
        oauth_req.sign_request(sign_method, consumer, tmp_token)
        self.logger.debug("----access this url and Press Authorize button to complete authorize:")
        self.logger.debug(oauth_req.to_url())
        raw_token = raw_input("Input oauth_token string and Press ENTER:")
        raw_token = raw_token
        req_token = oauth.OAuthToken.from_string(raw_token)
        assert tmp_token.key == req_token.key
        req_params = dict([part.split('=') for part in raw_token.split('&')])
        self.logger.debug(req_params)

        # req_token を access_tokenに交換する exchange_request_token_for_access_token
        params={'oauth_verifier':req_params['oauth_verifier']}
        oauth_req = oauth.OAuthRequest.from_consumer_and_token(
            consumer, token=tmp_token, http_url="https://www.evernote.com/oauth", parameters=params )
        oauth_req.sign_request(sign_method, consumer, tmp_token)
        url = oauth_req.to_url()
        self.logger.debug(url)
        connection.request(oauth_req.http_method, url)
        resp = connection.getresponse().read()
        self.logger.debug(resp)
        # response example
        access_token = oauth.OAuthToken.from_string(resp)
        self.logger.debug(access_token.key)

        # 期限切れの時間
        #expiredTime = time.time()+(authResult.expiration/1000.0-authResult.currentTime/1000.0)
        return access_token.key

    def create_note(self, data):
        # API URL 末尾のs1はs4までパターンがある
        # tokenの最初の数文字で判断できる
        shared = token_params["S"]
        noteStoreUri = "http://www.evernote.com/edam/note/"+shared
        noteStore = NoteStore.Client(TBinaryProtocol.TBinaryProtocol(THttpClient.THttpClient(noteStoreUri)))
        # ここで認証tokenを渡す。APIへのアクセスが発生
        notebooks = noteStore.listNotebooks(data["token"])
        # デフォルトのノートに設定されたnotebookを探索する
        for notebook in notebooks:
            if notebook.defaultNotebook:
                defaultNotebook = notebook
        # 投稿画像の設定
        image = open(data["filepath"], "r").read()
        md5 = hashlib.md5()
        md5.update(image)
        hashHex = md5.hexdigest()
        body = Types.Data()
        body.size = len(image)
        body.bodyHash = hashHex
        body.body = image
        resource = Types.Resource()
        resource.mime = data["mime"]
        resource.data = body
        # ノート本体の設定
        self.logger.debug('start Evernote create new note, title:"%s"' % (data["title"]))
        note = Types.Note()
        note.notebookGuid = defaultNotebook.guid
        # タイトルの先頭に半角スペースが入っているとエラーになってしまう
        note.title = data["title"].replace(" ", "", 3)
        note.content = '<?xml version="1.0" encoding="UTF-8"?>'
        note.content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml.dtd">'
        note.content += '<en-note>' + " " + '<br/>'
        note.content += '<en-media type="' + data["mime"] + '" hash="' + hashHex + '"/>'
        note.content += '</en-note>'
        note.created = int(time.time() * 1000)
        note.updated = note.created
        note.resources = [ resource ]
        # ノート生成実行
        return noteStore.createNote(data["token"], note)

    def post(self, data_):
        self.require_data = ["token", "filepath", "title", "mime", "email", "nickname"]
        data = self.data_decode(data_)
        if self.debug:
            data["token"] = self.auth_test()
        else:
            data['token'] = oauth.OAuthToken.from_string(data['token']).key

        token_params = dict([part.split('=') for part in data["token"].split(':')])
        if self.valid or self.debug:
            try:
                createdNote = self.create_note(data)
                if self.debug:
                    self.logger.debug(createdNote)
                    uri = "https://www.evernote.com/Home.action#v=t&n=%s&b=c" % createdNote.guid
                    self.logger.debug(uri)
                self.succeed()
                self.logger.debug("post succeed")
            except Exception, e:
                self.failed()
                tb = traceback.format_exc()
                self.logger.debug(tb)
                self.logger.warning(e)
        else:
            # 内部エラー。必要なデータが足りていない
            self.failed()
            self.logger.warning("invalid data:"+data)
