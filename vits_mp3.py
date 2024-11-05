from pydub import AudioSegment
import os
import sys
import numpy as np

import torch
import utils
import argparse

from scipy.io import wavfile
from text.symbols import symbols
from text import cleaned_text_to_sequence
from vits_pinyin import VITS_PinYin
import hashlib
import time
import logging

parser = argparse.ArgumentParser(description='Inference code for bert vits models')
parser.add_argument('--config', type=str, default='./configs/bert_vits.json')
parser.add_argument('--model', type=str, default='logs/bert_vits/G_3470000.pth')
args = parser.parse_args()



class VitsInfer():

    def __init__(self, model, config):
        # device
        self.device = torch.device("cpu")
        # self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # pinyin
        self.tts_front = VITS_PinYin("./bert", self.device)

        # config
        self.hps = utils.get_hparams_from_file(config)

        # model
        self.net_g = utils.load_class(self.hps.train.eval_class)(
            len(symbols),
            self.hps.data.filter_length // 2 + 1,
            self.hps.train.segment_size // self.hps.data.hop_length,
            **self.hps.model)
        utils.load_model(model, self.net_g)
        self.net_g.eval()
        self.net_g.to(self.device)

    def save_wav(self, wav, path, rate):
        wav *= 32767 / max(0.01, np.max(np.abs(wav))) * 0.6
        wavfile.write(path, rate, wav.astype(np.int16))

    def wav2mp3(self, wav_filename, mp3_filename):
        l = logging.getLogger("pydub.converter")
        l.setLevel(logging.ERROR)
        sourcefile = AudioSegment.from_wav(wav_filename)
        sourcefile.export(mp3_filename, format="mp3")

    def infer(self, text, length_scale=1.0, use_cache=True):
        md5 = hashlib.md5()
        val = text + ' ' + str(length_scale)
        md5.update(val.encode())
        filename = md5.hexdigest()
        os.makedirs('/data/tts/', exist_ok=True)
        pathname = os.path.join('/data/tts/', filename[:2])
        os.makedirs(pathname, exist_ok=True)
        wav_filename = os.path.join(pathname, filename + '.wav')
        mp3_filename = os.path.join(pathname, filename + '.mp3')
        if not use_cache or not os.path.isfile(mp3_filename): 
            phonemes, _ = self.tts_front.chinese_to_phonemes(text)
            input_ids = cleaned_text_to_sequence(phonemes)
            
            with torch.no_grad():
                x_tst = torch.LongTensor(input_ids).unsqueeze(0).to(self.device)
                x_tst_lengths = torch.LongTensor([len(input_ids)]).to(self.device)
                # x_tst_prosody = torch.FloatTensor(char_embeds).unsqueeze(0).to(self.device)
                audio = self.net_g.infer(x_tst, x_tst_lengths, noise_scale=0.5,
                                    length_scale=length_scale)[0][0, 0].data.cpu().float().numpy()
            self.save_wav(audio, wav_filename, self.hps.data.sampling_rate)
            self.wav2mp3(wav_filename, mp3_filename)

        return mp3_filename

if __name__ == "__main__":
    vits = VitsInfer(args.model, args.config)
        # print('{} {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), tokenModel.model_dump()))
    start = time.time()
    respond = vits.infer("我们在北京语言大学呢", use_cache=False)
    end = time.time()

    print(end-start)
    