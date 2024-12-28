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

parser = argparse.ArgumentParser(description='Inference code for bert vits models')
parser.add_argument('--config', type=str, default='./configs/bert_vits.json')
parser.add_argument('--model', type=str, default='logs/bert_vits/G_2170000.pth')
args = parser.parse_args()

def save_wav(wav, path, rate):
    wav *= 32767 / max(0.01, np.max(np.abs(wav))) * 0.6
    wavfile.write(path, rate, wav.astype(np.int16))

# device
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
device = torch.device("cpu")

# pinyin
tts_front = VITS_PinYin("./bert", device)

# config
hps = utils.get_hparams_from_file(args.config)

# model
net_g = utils.load_class(hps.train.eval_class)(
    len(symbols),
    hps.data.filter_length // 2 + 1,
    hps.train.segment_size // hps.data.hop_length,
    **hps.model)

# model_path = "logs/bert_vits/G_1130000.pth"
# utils.save_model(net_g, "vits_bert_model.pth")
# model_path = "vits_bert_model.pth"
utils.load_model(args.model, net_g)
net_g.eval()
net_g.to(device)

def make_phrase_tts(phrase_filename, out_path):
    os.makedirs(out_path, exist_ok=True)
    n = 0
    f = open(phrase_filename, "r", encoding='utf-8')
    for line in f:
        items = line.strip().split()
        if len(items) > 1:
            n = n + 1
            phrase = items[1]
            if os.path.isfile(f"{out_path}/{phrase}.wav"):
                continue
            print(f"processing {n} {phrase}")
            phonemes, char_embeds = tts_front.chinese_to_phonemes(phrase)
            input_ids = cleaned_text_to_sequence(phonemes)
            with torch.no_grad():
                x_tst = torch.LongTensor(input_ids).unsqueeze(0).to(device)
                x_tst_lengths = torch.LongTensor([len(input_ids)]).to(device)
                x_tst_prosody = None
                # x_tst_prosody = torch.FloatTensor(char_embeds).unsqueeze(0).to(device)
                audio = net_g.infer(x_tst, x_tst_lengths, bert=x_tst_prosody, noise_scale=0.5,
                                    length_scale=1.0)[0][0, 0].data.cpu().float().numpy()
            save_wav(audio, f"{out_path}/{phrase}.wav", hps.data.sampling_rate)
    f.close()

if __name__ == "__main__":
    make_phrase_tts("./all.txt", "./all_out")
