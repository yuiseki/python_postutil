# -*- coding: utf-8 -*-
import multiprocessing
import simplejson as json
import pickle

filepath = "/home/yuiseki/Photos/miu.jpg"
title = "hoge"
email = "yuiseki@gmail.com"
dic = {'filepath':filepath, 'title':title, 'email':email, 'nickname':'yuiseki'}

# 各スクリプトの投稿テストを行う
if False:
    print("----starting test of picasa client----")
    from picasa import PostPicasaUtil
    dic["filename"] = "hoge.jpg"
    data = pickle.dumps(dic)
    PostPicasaUtil(data)
    print("----done picasa test----")

if True:
    print("----starting test of evernote client----")
    from evernote_post import PostEvernoteUtil
    data = pickle.dumps(dic)
    PostEvernoteUtil(data)
    print("----done dropbox test----")

if False:
    print("----starting test of flickr client----")
    from flickr import PostFlickrUtil
    dic["is_public"] = 0
    data = pickle.dumps(dic)
    PostFlickrUtil(data)
    print("----done flickr test----")


if False:
    print("----starting test of dropbox client----")
    from dropbox_post import PostDropboxUtil
    dic["filename"] = "hoge.jpg"
    data = pickle.dumps(dic)
    PostDropboxUtil(data)
    print("----done dropbox test----")


