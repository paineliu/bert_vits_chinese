from pydub import AudioSegment

def wav2mp3(wav_filename, mp3_filename):
    sourcefile = AudioSegment.from_wav(wav_filename)
    sourcefile.export(mp3_filename, format="mp3")

wav2mp3('./vits_infer_out/bert_vits_1.wav', './vits_infer_out/bert_vits_1.mp3')