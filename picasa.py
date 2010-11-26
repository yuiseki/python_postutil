# -*- coding: utf-8 -*-
import sys
import traceback
from postutil import PostUtil
import gdata
import gdata.photos.service
import gdata.media

class PostPicasaUtil(PostUtil):
    def __init__(self, data_):
        self.service_name = "picasa"
        PostUtil.__init__(self)
        self.post(data_)

    def get_client(self, token):
        # debug環境ではtokenは無視する
        gd_client = gdata.photos.service.PhotosService()
        if self.debug:
            import getpass
            gd_client.email = raw_input('Enter your gmail addr: ')
            gd_client.password = getpass.getpass('Enter your google password: ')
            gd_client.source = 'exampleCo-exampleApp-1'
            gd_client.ProgrammaticLogin()
            return gd_client
        else:
            gd_client.auth_token = token
            gd_client.UpgradeToSessionToken()
            return gd_client

    def post(self, data_):
        self.require_data = ["token", "filepath", "filename", "mime", "title", "email", "nickname"]
        data = self.data_decode(data_)
        if self.debug: data['token'] = ''
        if self.debug: self.logger.debug(data)

        gd_client = self.get_client(data['token'])
        if self.valid or self.debug:
            try:
                #album_url = '/data/feed/api/user/%s/albumid/%s' % (username, album.gphoto_id.text)
                album_url = '/data/feed/api/user/default/albumid/default' # dropbox
                # gdata.photos.PhotoEntry or GooglePhotosException
                photo = gd_client.InsertPhotoSimple(album_url, data['filename'],
                        data['title'], data['filepath'], content_type=data["mime"])
                self.succeed()
                #self.logger.debug(photo)
            except gdata.photos.service.GooglePhotosException, e:
                self.failed()
                tb = traceback.format_exc()
                self.logger.debug(tb)
                self.logger.debug('GooglePhotosException error_code: %s' % e.error_code)
            except Exception, e:
                self.failed()
                tb = traceback.format_exc()
                self.logger.debug(tb)
                self.logger.warning(e)
        else:
            # 内部エラー。必要なデータが足りていない
            self.failed()
            self.logger.warning("invalid data: "+data)

