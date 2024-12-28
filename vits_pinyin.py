import re

from tn.chinese.normalizer import Normalizer

from pypinyin import lazy_pinyin, Style
from pypinyin.core import load_phrases_dict
from pypinyin.contrib.tone_convert import to_tone3
from text import pinyin_dict
from bert import TTSProsody
import torch

def is_chinese(uchar):
    if uchar >= u'\u4e00' and uchar <= u'\u9fa5':
        return True
    else:
        return False


def clean_chinese(text: str):
    text = text.strip()
    text_clean = []
    for char in text:
        if (is_chinese(char)):
            text_clean.append(char)
        else:
            if len(text_clean) > 1 and is_chinese(text_clean[-1]):
                text_clean.append(',')
    text_clean = ''.join(text_clean).strip(',')
    return text_clean


def load_pinyin_dict():
    my_dict={}
    with open("./text/pinyin-local.txt", "r", encoding='utf-8') as f:
        content = f.readlines()
        for line in content:
            cuts = line.strip().split()
            hanzi = cuts[0]
            phone = cuts[1:]
            tmp = []
            for p in phone:
                tmp.append([p])
            my_dict[hanzi] = tmp
    load_phrases_dict(my_dict)


class VITS_PinYin:
    def __init__(self, bert_path, device, hasBert=True):
        # load_pinyin_dict()
        self.hasBert = hasBert
        if self.hasBert:
            self.prosody = TTSProsody(bert_path, device)
        self.normalizer = Normalizer()

    def get_phoneme4pinyin(self, pinyins):
        result = []
        count_phone = []
        for pinyin in pinyins:
            if pinyin[:-1] in pinyin_dict:
                tone = pinyin[-1]
                a = pinyin[:-1]
                a1, a2 = pinyin_dict[a]
                result += [a1, a2 + tone]
                count_phone.append(2)
        return result, count_phone
    
    def text_to_words(self, text):
        words = re.split(r"([\(\)])", text)
        return words

    def get_fix_pinyin(self, text):
        sents = self.text_to_words(text)
        words = ''
        map_fix_pinyin = {}
        skip = False
        for i in range(len(sents)):
            if sents[i] == '(' and len(sents) > i:
                pos = len(words)
                if (pos > 0):
                    pos -= 1
                map_fix_pinyin[pos] = sents[i+1]
                skip = True
            elif sents[i] == ')':
                skip = False
            else:
                if not skip:
                    words += sents[i]
        return words, map_fix_pinyin

    def chinese_to_phonemes(self, text):
        # pinyins = text.split(' ')
        # is_pinyin3 = True
        # pinyin3_lst = []
        # for pinyin in pinyins:
        #     pinyin3 = self.pinyin_to_tone3(pinyin)
        #     if not pinyin3.isalnum():
        #         is_pinyin3 = False
        #         break
        #     pinyin3_lst.append(pinyin3)

        # if is_pinyin3:
        #     char_embeds = ''
        #     phonemes = ["sil"]
        #     sub_p, sub_c = self.get_phoneme4pinyin(pinyin3_lst)
        #     phonemes.extend(sub_p)
        #     phonemes.append("sp")
        #     phonemes.append("sil")
        #     return " ".join(phonemes), char_embeds

            
        text, map_pinyin_fix = self.get_fix_pinyin(text)
        text = self.normalizer.normalize(text)
        text = clean_chinese(text)
        phonemes = ["sil"]
        chars = ['[PAD]']
        count_phone = []
        count_phone.append(1)
        for subtext in text.split(","):
            if (len(subtext) == 0):
                continue
            pinyins = self.correct_pinyin_tone3(subtext)
            for each in map_pinyin_fix:
                pinyins[each] = map_pinyin_fix[each]
            sub_p, sub_c = self.get_phoneme4pinyin(pinyins)
            phonemes.extend(sub_p)
            phonemes.append("sp")
            count_phone.extend(sub_c)
            count_phone.append(1)
            chars.append(subtext)
            chars.append(',')
        phonemes.append("sil")
        count_phone.append(1)
        chars.append('[PAD]')
        chars = "".join(chars)
        char_embeds = None
        if self.hasBert:
            char_embeds = self.prosody.get_char_embeds(chars)
            char_embeds = self.prosody.expand_for_phone(char_embeds, count_phone)
        return " ".join(phonemes), char_embeds

    def correct_pinyin_tone3(self, text):
        pinyin_list = lazy_pinyin(text,
                                  style=Style.TONE3,
                                  strict=False,
                                  neutral_tone_with_five=True,
                                  tone_sandhi=True)
        # , tone_sandhi=True -> 33变调
        return pinyin_list

    def pinyin_to_tone3(self, text):
        return to_tone3(text)


if __name__ == "__main__":
    n = 0

    # pinyin
    tts_front = VITS_PinYin("./bert", torch.device("cpu"))

    fo = open("vits_infer_item.txt", "r+", encoding='utf-8')
    while (True):
        try:
            item = fo.readline().strip()
        except Exception as e:
            print('nothing of except:', e)
            break
        if (item == None or item == ""):
            break
        n = n + 1
        phonemes, char_embeds = tts_front.chinese_to_phonemes(item)
    fo.close()
