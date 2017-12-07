import wave
import numpy as np
import string
import sys

def read_wave_data(file_path):
    # open a wave file, and return a Wave_read object
    f = wave.open(file_path, "rb")
    # read the wave's format infomation,and return a tuple
    params = f.getparams()
    # get the info
    nchannels, sampwidth, framerate, nframes = params[:4]
    # Reads and returns nframes of audio, as a string of bytes.
    str_data = f.readframes(nframes)
    # close the stream
    f.close()
    # turn the wave's data to array
    wave_data = np.fromstring(str_data, dtype=np.short)
    # for the data is stereo,and format is LRLRLR...
    # shape the array to n*2(-1 means fit the y coordinate)
    # transpose the data
    wave_data = wave_data.T
    # calculate the time bar
    time = np.arange(0, nframes) * (1.0 / framerate)
    return wave_data, time

def getExtensionWav(firstWavData, firstStart, firstEnd, secondWavData, secondStart, secondEnd, samplerate=384000,
               extension=0):
    # get index after extension
    start = max(0, min(firstStart, secondStart) * samplerate - extension)
    maxSize = min(len(firstWavData), len(secondWavData))
    end = min(maxSize, max(firstEnd, secondEnd) * samplerate + extension)
    # return data after extension
    return firstWavData[start: end], secondWavData[start: end]

def analysisFile(path):
    file = open(path)
    datas = file.readlines()
    size = 0
    indexline = 0
    count = 0
    result = []
    realSize = 0
    for data in datas:
        d = data.split(" ")
        if 'intervals:' in d and 'size' in d:
            size = string.atoi(d[len(d) - 1])
            indexline = count
            break
        count += 1
    for i in range(size):
        lineText = datas[i * 4 + 4 +  indexline]
        if 'text = "<p:>"' in lineText:
            continue
        xmaxText = datas[i * 4 + 3 + indexline].strip('\n').split(" ")
        xmax = string.atof(xmaxText[len(xmaxText) - 1])
        xminText = datas[i * 4 + 2 + indexline].strip('\n').split(" ")
        xmin = string.atof(xminText[len(xminText) - 1])
        result.append([xmin, xmax])
        realSize += 1
    file.close()
    return realSize, result

def gcc_phat(sig, refsig, fs=1, max_tau=None, interp=1):
     '''
     This function computes the offset between the signal sig and the reference signal refsig
     using the Generalized Cross Correlation - Phase Transform (GCC-PHAT)method.
     '''

     # make sure the length for the FFT is larger or equal than len(sig) + len(refsig)
     n = sig.shape[0] + refsig.shape[0]
     # Generalized Cross Correlation Phase Transform
     SIG = np.fft.rfft(sig, n=n)
     REFSIG = np.fft.rfft(refsig, n=n)
     R = SIG * np.conj(REFSIG)
     cc = np.fft.irfft(R / np.abs(R), n=(interp * n))

     max_shift = int(interp * n / 2)
     if max_tau:
         max_shift = np.minimum(int(interp * fs * max_tau), max_shift)

     cc = np.concatenate((cc[-max_shift:], cc[:max_shift+1]))

     # find max cross correlation index
     shift = np.argmax(np.abs(cc)) - max_shift

     tau = shift / float(interp * fs)
     return tau, cc


# get datas calculated to correlation
def inputCorrelation(wave1_data, phonemes1, wave2_data, phonemes2, phonemeSize, extensionWav):
    correlation = []
    for i in range(phonemeSize):
        data1, data2 = getExtensionWav(wave1_data, phonemes1[i][0], phonemes1[i][1], wave2_data, phonemes2[i][0], phonemes2[i][1],extension=extensionWav)
        tau, cc = gcc_phat(data1, data2)
        if tau >= (len(data1) / 2.0):
            tau = len(data1) - tau
        correlation.append(tau)
    return correlation

def main():
    filename1 = sys.argv[1]
    filename2 = sys.argv[2]
    filenameGrid1 = sys.argv[3]
    filenameGrid2 = sys.argv[4]
    # read .wav file
    wave1_data, time1 = read_wave_data(filename1)
    wave2_data, time2 = read_wave_data(filename2)
    # analysis .TextGrid file
    phonemesSize1, phonemesResult1 = analysisFile(filenameGrid1)
    phonemesSize2, phonemesResult2 = analysisFile(filenameGrid2)
    if phonemesSize1 != phonemesSize2:
        print "Error!!!"
    correlations = inputCorrelation(wave1_data, phonemesResult1, wave2_data, phonemesResult2, phonemesSize1, 0)
    print correlations
if __name__ == "__main__":
    main()
