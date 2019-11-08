import re
import os
import emoji
import neologdn

list_tmp = []

f = open('tweets1.txt')
list_text = f.read()
f.close()

# list_text = list_text.split("\n")
list_text = list_text.split(" ")
# print(list_text)
# print(list_text[10])

#以下正規表現による前処理
for text in list_text:
    text_tmp = text
    text_tmp = re.sub('RT.*', '', text_tmp)
    text_tmp = re.sub('@.*', '', text_tmp)
    text_tmp = re.sub('http.*', '', text_tmp)
    text_tmp = re.sub('#.*', '', text_tmp)
    text_tmp = re.sub('\n', '', text_tmp)
    text_tmp = text_tmp.strip()
    if text_tmp != '':
        list_tmp.append(text_tmp)

# list_tmp = list(set(list_tmp))
text = ','.join(list_tmp)

#全角、数字等を統一
normalized_text = neologdn.normalize(text)
text_without_emoji = ''.join(['' if c in emoji.UNICODE_EMOJI else c for c in normalized_text])
    
#桁区切りの除去と数字の置換
tmp = re.sub(r'(\d)([,.])(\d+)', r'\1\3', text_without_emoji)
text_replaced_number = re.sub(r'\d+', '0', tmp)

#記号の置き換え(半角・全角)
tmp = re.sub(r'[!-/:-@[-`{-~]', r' ', text_replaced_number)
text_removed_symbol = re.sub(u'[■-♯]', ' ', tmp)


print(text_removed_symbol)