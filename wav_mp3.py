import shutil
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
parser.add_argument('--model', type=str, default='logs/bert_vits/G_2170000.pth')
args = parser.parse_args()



class VitsInfer():

    def __init__(self, wav_path, mp3_path, move_path):
        # device
        self.wav_path = wav_path
        self.mp3_path = mp3_path
        self.move_path = move_path
    
    def process(self):
        #递归遍历文件夹
        for root, dirs, files in os.walk(self.wav_path):
            for file in files:
                if file.endswith(".wav"):
                    wav_filename = os.path.join(root, file)
                    mp3_filename = wav_filename.replace(".wav", ".mp3")
                    mp3_filename = mp3_filename.replace(self.wav_path, self.mp3_path)
                    os.makedirs(os.path.dirname(mp3_filename), exist_ok=True)
                    self.wav2mp3(wav_filename, mp3_filename)
    def move(self):
        #递归遍历文件夹
        for root, dirs, files in os.walk(self.mp3_path):
            for file in files:
                if file.endswith(".mp3"):
                    mp3_filename = os.path.join(root, file)
                    move_filename = mp3_filename.replace(self.mp3_path, self.move_path)
                    os.makedirs(os.path.dirname(move_filename), exist_ok=True)
                    word = os.path.basename(file).split(".")[0]
                    if len(word) == 1:
                        print(word)
                    else:
                        shutil.move(mp3_filename, move_filename)

    def wav2mp3(self, wav_filename, mp3_filename):
        print(f"wav2mp3: {wav_filename} -> {mp3_filename}")
        l = logging.getLogger("pydub.converter")
        l.setLevel(logging.ERROR)
        sourcefile = AudioSegment.from_wav(wav_filename)
        sourcefile.export(mp3_filename, format="mp3")
        return mp3_filename

if __name__ == "__main__":
        # print('{} {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), tokenModel.model_dump()))
    start = time.time()
    vits = VitsInfer('./ci_out', './ci_out_word', './ci_out_mp3')
    # vits.process()
    vits.move()
    end = time.time()

    print(end-start)
    