# _*_ coding: utf-8 _*_

from requests_oauthlib import OAuth1Session
import json
import datetime, time, sys
from abc import ABCMeta, abstractmethod
import codecs
import json
import urllib
import pprint
import requests
import emoji
import re
import neologdn

#クエリ変更
since = '2019-10-30'
until = '2019-10-31'
#イベント変更
event_name = '川越'
#取得件数変更
tweetsTotal = -1

# 位置情報からランドマークを取得
# appid = "dj00aiZpPUJ5WHY4VUpITjdYQSZzPWNvbnN1bWVyc2VjcmV0Jng9ZjY-"

# base_url = "https://map.yahooapis.jp/placeinfo/V1/get"
# lat = "35.706779"
# lon = "139.659377"

# output = "json"

# url = base_url + "?lat=%s&lon=%s&appid=%s&output=%s" % (lat,lon,appid,output)

# json_tree = json.loads(urllib.request.urlopen(url).read())

# area = json_tree["ResultSet"]["Area"]

# land_mark = [area.get('Name') for area in area]

# # land_mark = land_mark[0]

# pprint.pprint(land_mark)

# # pprint.pprint(json_tree)


# ランドマーク検索
CK = 'LCbxN48DRXsEQYrlY2TTWw'
CS = 'gqkzuQHksJBfBC41KQARK2b36pkbKkkh8ZbMaivD4'
AT = '531189976-WdrvuaKDAuqAgdBlMJPPqTM1FlgttM7I8qzaFlYZ'
AS = 'sSbVjNx8sJ8Rb28fq8QmUEXl8gRjp1xalrtTsCyL3SlaJ'

class GetTweets(object):
    __metaclass__ = ABCMeta
    
    def __init__(self):
        self.session = OAuth1Session(CK, CS, AT, AS)
    
    @abstractmethod
    def specifyUrlAndParams(self, keyword):
        '''
            呼び出し先 URL,パラメーターを返す
            '''
    
    @abstractmethod
    def pickupTweet(self, res_text, includeRetweet):
        '''
            res_textからツイートを取り出し配列にセットして返却
            '''
    
    @abstractmethod
    def getLimitContext(self, res_text):
        '''
            回数制限の情報を取得
            '''
    
    def collect(self, total = -1, onlyText = False, includeRetweet = False):
        '''
            ツイート取得を開始
            '''
        
        #回数制限を確認
        self.checkLimit()
        
        #URL,parameter
        url, params = self.specifyUrlAndParams()
        params['include_rts'] = str(includeRetweet).lower()
        
        #ツイート取得
        cnt = 0
        unavailableCnt = 0
        while True:
            res = self.session.get(url, params = params)
            print(params)
            if res.status_code == 503:
            #503:Service is Unavailable
                if unavailableCnt > 10:
                    raise Exception('Twitter API error %d' % res.status_code)

                unavailableCnt += 1
                print('Service Unavailable 503')
                self.waitUntilReset(time.mktime(datetime.now().timeuple()) + 30)
                continue

            unavailableCnt = 0

            if res.status_code != 200:
                raise Exception('Twitter API error %d' % res.status_code)

            tweets = self.pickupTweet(json.loads(res.text))
            if len(tweets) == 0:
                break
        
            for tweet in tweets:
                if(('retweeted_status' in tweet) and (includeRetweet is False)):
                    pass
                else:
                    if onlyText is True:
                        yield tweet['text']
                    else:
                        yield tweet

                cnt += 1
                if cnt %100 == 0:
                    print('%d件' % cnt)

                if total > 0 and cnt >= total:
                    return
                
            params['max_id'] = tweet['id'] - 1

            #ヘッダ確認

            if('X-Rate-Limit-Remaining' in res.headers and 'X-Rate-Limit-Reset' in res.headers):
                if (int(res.headers['X-Rate-Limit-Remaining']) == 0):
                    self.waitUntilReset(int(res.headers['X-Rate-Limit-Reset']))
                    self.checkLimit()
            else:
                print ('not found  -  X-Rate-Limit-Remaining or X-Rate-Limit-Reset')
                self.checkLimit()
    def checkLimit(self):
            '''
            回数制限を問合せ、アクセス可能になるまで wait する
            '''
            unavailableCnt = 0
            while True:
                url = "https://api.twitter.com/1.1/application/rate_limit_status.json"
                res = self.session.get(url)
 
                if res.status_code == 503:
                    # 503 : Service Unavailable
                    if unavailableCnt > 10:
                        raise Exception('Twitter API error %d' % res.status_code)
 
                    unavailableCnt += 1
                    print ('Service Unavailable 503')
                    self.waitUntilReset(time.mktime(datetime.datetime.now().timetuple()) + 30)
                    continue
 
                unavailableCnt = 0
 
                if res.status_code != 200:
                    raise Exception('Twitter API error %d' % res.status_code)
 
                remaining, reset = self.getLimitContext(json.loads(res.text))
                if (remaining == 0):
                    self.waitUntilReset(reset)
                else:
                    break
 
    def waitUntilReset(self, reset):
        seconds = reset - time.mktime(datetime.datetime.now().timetuple())
        seconds = max(seconds, 0)
        print ('\n     =====================')
        print ('     == waiting %d sec ==' % seconds)
        print ('     =====================')
        sys.stdout.flush()
        time.sleep(seconds + 10)  # 念のため + 10 秒
 
    @staticmethod
    def bySearch(keyword):
        return TweetsGetterBySearch(keyword)
 
    @staticmethod
    def byUser(screen_name):
        return TweetsGetterByUser(screen_name)
 
 
class TweetsGetterBySearch(GetTweets):
    '''
    キーワードでツイートを検索
    '''
    def __init__(self, keyword):
        super(TweetsGetterBySearch, self).__init__()
        self.keyword = keyword
        
    def specifyUrlAndParams(self):
        '''
        呼出し先 URL、パラメータを返す
        '''
        url = 'https://api.twitter.com/1.1/search/tweets.json'
        query = self.keyword

        # print(query)
        params = {
            'q':query, 
            # 'since':since, 
            # 'until':until, 
            'count':10
            }

        return url, params
 
    def pickupTweet(self, res_text):
        '''
        res_text からツイートを取り出し、配列にセットして返却
        '''
        results = []
        for tweet in res_text['statuses']:
            results.append(tweet)
 
        return results
 
    def getLimitContext(self, res_text):
        '''
        回数制限の情報を取得 （起動時）
        '''
        remaining = res_text['resources']['search']['/search/tweets']['remaining']
        reset     = res_text['resources']['search']['/search/tweets']['reset']
 
        return int(remaining), int(reset)
    
 
class TweetsGetterByUser(GetTweets):
    '''
    ユーザーを指定してツイートを取得
    '''
    def __init__(self, screen_name):
        super(TweetsGetterByUser, self).__init__()
        self.screen_name = screen_name
        
    def specifyUrlAndParams(self):
        '''
        呼出し先 URL、パラメータを返す
        '''
        url = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
        params = {'screen_name':self.screen_name, 'count':200}
        return url, params
 
    def pickupTweet(self, res_text):
        '''
        res_text からツイートを取り出し、配列にセットして返却
        '''
        results = []
        for tweet in res_text:
            results.append(tweet)
 
        return results
 
    def getLimitContext(self, res_text):
        '''
        回数制限の情報を取得 （起動時）
        '''
        remaining = res_text['resources']['statuses']['/statuses/user_timeline']['remaining']
        reset     = res_text['resources']['statuses']['/statuses/user_timeline']['reset']
 
        return int(remaining), int(reset)


    def remove(src_str):
        tweet = ''.join(c for c in src_str if c not in emoji.UNICODE_EMOJI)

        return tweet


 
if __name__ == '__main__':
 
    # キーワードで取得
    getter = GetTweets.bySearch(event_name)
    
    # ユーザーを指定して取得 （screen_name）
    # getter = GetTweets.byUser('bar310lv')

    #期間を指定して取得

    f = codecs.open('/Users/oybn/fasttext/tweets%s.txt' % event_name, 'w', 'utf-8')
    
    cnt = 0
    list_tmp = []
    list_text = []

    for tweet in getter.collect(total = tweetsTotal):
        cnt += 1
        # print ('------ %d' % cnt)
        # print ('{} {} {}'.format(tweet['id'], tweet['created_at'], '@'+tweet['user']['screen_name']))
        # print (tweet['text'])
        # f.write('——————————————–')
        # f.write('\n')
        # f.write(str(tweet['id']))
        # f.write('\n')
        # f.write(tweet['created_at'])
        # f.write('\n')
        # f.write(tweet['user']['screen_name'])
        # f.write('\n')

        print(tweet['text'])
        print('\n')
        f.write(tweet['text'])
        f.write('\n')

        list_text.append(tweet['text'])
    
    f.close()

   



