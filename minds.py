
#from subprocess import _TXT
from asyncore import write
from urllib import response
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import random
from itertools import islice
from pyparsing import re
import requests
import calendar
import time
from random import randint 

DB_COMMENTS = "/comments"
DB_TOKEN = "/accessToken"
DB_COMMENTED = "/commentedId"


cred = credentials.Certificate("minds-ca12d-firebase-adminsdk-ibo6f-01322abe83.json")
#firebase_admin.initialize_app(cred)
default_app = firebase_admin.initialize_app(cred, {
	'databaseURL': 'https://minds-ca12d-default-rtdb.asia-southeast1.firebasedatabase.app/'
	})

comments_ref = db.reference(DB_COMMENTS)
commented_ref = db.reference(DB_COMMENTED)
token_rf = db.reference(DB_TOKEN)

maxComment = 1000
maxDelay = 15

def checkComment(commentId):
    return commented_ref.child(commentId).get() == True

def checkVisible(postId):
    url = "https://www.minds.com/api/v2/entities/?urns=urn%3Aactivity%3A" + postId
    print(url)
    response = requests.get(url)
    jsonResponse = response.json()
    if len(jsonResponse['entities']) > 0:
        entitiId = jsonResponse['entities'][0]['entity_guid']
        if isinstance(entitiId, str):
            return True, entitiId
        else:
            return True, jsonResponse['entities'][0]['guid']
        
    else:
        return False, ""
def getComment(postId, comments):
    url = comments[postId]
    if "9gag" in url:
        print("This is 9gag post")
        prefix = "https://comment-cdn.9gag.com/v2/cacheable/comment-list.json?appId=a_dd8f2b7d304a10edaf6f29517ea0ca4100a43d1b&count=10&url="
        urlSurFix = url.replace("/", "%2F").replace("s:", "%3A")
        requestUrl = prefix + urlSurFix
        print("Comment resoure API: " + requestUrl)
        response = requests.get(requestUrl)
        cmts = response.json()['payload']['comments']
        if len(cmts) == 0:
            print("9GAG post has no comment")
            return "", ""
        value = randint(0, len(cmts) - 1)
        data = cmts[value]
        text = data['mediaText']
        if text == "":
            value = randint(0, len(cmts) - 1)
            data = cmts[value]
            text = data['mediaText']
        if text == "":
            value = randint(0, len(cmts) - 1)
            data = cmts[value]
            text = data['mediaText']
        if text == "":
            print("9GAG comment has no text comment")
            return "", ""
        return data['commentId'], text
    if "gab" in url:
        print("This is Gab post")
        return "", ""
        pre = "https://gab.com/api/v1/comments/"
        sur = "?sort_by=most-liked"
        gabPostArray = url.split("/")
        gabPostId = gabPostArray[-1]
        requestUrl = pre + gabPostId + sur
        print("Comment resoure API: " + requestUrl)
        response = requests.get(requestUrl)
        print(response.json())
        return "0002", "hahah"

    
def writeCommentedData(id):
    commented_ref.child(id).set(True)
    print("UPDATED Commented " + id)
def viewPost(postID, accessToken):
    url = "https://www.minds.com/api/v2/analytics/views/activity/" + postID
    pvUrl = "https://www.minds.com/api/v2/mwa/pv"
    ts = calendar.timegm(time.gmtime())
    params = {
        "platform": "web",
        "campaign": "",
        "medium": "",
        "source": "",
        "salt": "",
        "page_token": "",
        "delta": 0,
        "timestamp": ts,
        "position": 0
    }
    pvParam = {
        "url": "/newsfeed/"+ postID,
        "referrer": ""
    }
    headers = {"Authorization": "Bearer " + accessToken}
    response = requests.post(url, data=params, headers= headers)
    pvRes = requests.post(pvUrl, data=pvParam, headers= headers)
    print("View " + postID + " " + response.json()["status"])
    print("PV " + postID + " " + pvRes.json()["status"])

def comment(postId, text, accessToken):
    url = "https://www.minds.com/api/v1/comments/" + postId
    params = {
            "is_rich": 0,
            "title": "",
            "description": "",
            "thumbnail": "",
            "url": "",
            "mature": 0,
            "access_id": 2,
            "comment": text,
            "parent_path": "0:0:0"
    }
    headers = {"Authorization": "Bearer " + accessToken}
    response = requests.post(url, data=params, headers= headers)
    if check_key_exist(response.json(), 'status'):
        print("SUCCESS *** Commented " + text + " to " + postId + " " + response.json()['status'])
    else:
        print(response.json())
def check_key_exist(test_dict, key):
    try:
       test_dict[key]
       return True
    except KeyError:
        return False

def start():
    delayTime = maxDelay
    commentedCount = 0
    while True:
        if delayTime == 0:
            delayTime = maxDelay
        else:
            delayTime -= 1
        mins, secs = divmod(delayTime, 60)
        timer = '<COMMENTTED: ' + str(commentedCount) +  '> Restart in: {:02d}:{:02d}'.format(mins, secs)
        print(timer, end="\r")

        if delayTime == maxDelay: 
            comments = comments_ref.get()
            token = token_rf.get()
            commented = commented_ref.get()
            print("Restarting")
            list(islice(comments.items(),maxComment))
            postID = random.choice(list(comments))
            user = random.choice(list(token))
            accessToken = token[user]
            print('Using ' + user)
            visible, entitiID = checkVisible(postID)
            if visible and isinstance(entitiID, str):
                print("Post " + postID + " visible")
                viewPost(postID, accessToken)
                (commentID, commentText) = getComment(postID, comments)
                if check_key_exist(commented, commentID) == False:
                    print("DATA *** Commented Data: " + str(len(commented.keys())))
                    if commentID != "":
                        print("Commenting " + commentText + " from " + user + " to " + postID)
                        writeCommentedData(commentID)
                        comment(entitiID, commentText, accessToken)
                        commentedCount += 1
                    else:
                        print("ERROR *** CommentID is empty")
                else:
                    print("ERROR *** This comment has commented " + commentID + " ----")
            else:
                print("ERROR *** " + postID + " not visible")
        time.sleep(1)
        
start()