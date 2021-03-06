# -*- coding: utf-8 -*-
"""파형분할.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1y3FZy40q_d0BF1hWhn94PTdjXG2MoGDP
"""

!pip install biosppy

import biosppy
import scipy

from google.colab import drive
drive.mount('/content/drive')

!pip install wfdb

!pip install neurokit2

# Commented out IPython magic to ensure Python compatibility.
import matplotlib.pyplot as plt
# %matplotlib inline
import numpy as np
import pandas as pd
from pathlib import Path
import re
import wfdb
from wfdb import processing

data_dir = Path('/content/drive/My Drive/딥러닝/physionet.org/files/ludb/1.0.0')

num_records = 200
records = []
for i in range(1,num_records+1):
    record = wfdb.io.rdrecord(f'{data_dir}/{i}')
    age = 99 if record.comments[0][7:] == '>89' else int(record.comments[0][7:])
    data = {'id': i,
            'age(10)' : age //10 * 10, 
            
            'sex':record.comments[1][-1],
            'dignosis':record.comments[3:]}
    cols = ['i', 'ii',  'iii',  'avr',  'avl',  'avf',  'v1',  'v2',  'v3',  'v4',  'v5',  'v6']
    for col, j in zip(cols, range(12)):
        ann = wfdb.rdann(f'{data_dir}/{i}', f'atr_{col}')
        data[col] = {'singal':record.p_signal[:, j], 'anno': ann.__dict__['symbol'], 'anno_idx': ann.__dict__['sample']}
    records.append(data)

"""1. records[0]['i'] 기준으로 파형분할 한번 돌려보기 """

records[0]['i']['anno_idx']

anno = []
for ann in records[0]['i']['anno_idx']:
  anno.append(records[0]['i']['singal'][ann])

#기존 데이터 파형 분할 시각화
xpos = list(range(0, 5000))
print(xpos)


pyplot.rcParams["font.size"] = 20
pyplot.rcParams["figure.figsize"] = (20, 10)
pyplot.figure()
pyplot.legend()
pyplot.grid()
pyplot.title('id:1 , signal Time Series')
pyplot.xlabel('10Seconds with 500Hz')
pyplot.ylabel('signal')
plt.plot(xpos, signal_1)
plt.scatter(records[0]['i']['anno_idx'],anno, marker='o', c='r')

plt.show()

from scipy.signal import find_peaks
import neurokit as nk

!pip install systole

#r 피크점 찾기
def ecg_find_peaks(signal, sampling_rate=1000):
    rpeaks, = biosppy.ecg.hamilton_segmenter(np.array(signal), sampling_rate=sampling_rate)
    rpeaks, = biosppy.ecg.correct_rpeaks(signal=np.array(signal), rpeaks=rpeaks, sampling_rate=sampling_rate, tol=0.05)
    return(rpeaks)

#이외 피크점 및 onset, offset 찾기
def ecg_wave_detector(ecg, rpeaks):
    q_waves = []
    p_waves = []
    p_waves_starts = []
    q_waves_starts = []
    s_waves = []
    t_waves = []
    t_waves_starts = []
    t_waves_ends = []
    for index, rpeak in enumerate(rpeaks[:-3]):

        try:
            epoch_before = np.array(ecg)[int(rpeaks[index-1]):int(rpeak)]
            epoch_before = epoch_before[int(len(epoch_before)/2):len(epoch_before)]
            epoch_before = list(reversed(epoch_before))

            q_wave_index = np.min(find_peaks(epoch_before)[0])
            q_wave = rpeak - int(q_wave_index)
            p_wave_index = q_wave_index + np.argmax(epoch_before[q_wave_index:])
            p_wave = rpeak - p_wave_index

            inter_pq = epoch_before[q_wave_index:p_wave_index]
            inter_pq_derivative = np.gradient(inter_pq, 2)
            q_start_index = nk.find_closest_in_list(len(inter_pq_derivative)/2, find_peaks(inter_pq_derivative)[0])
            q_start = q_wave - q_start_index

            q_waves.append(q_wave)
            p_waves.append(p_wave)
            q_waves_starts.append(q_start)
        except ValueError:
            pass
        except IndexError:
            pass

        try:
            epoch_after = np.array(ecg)[int(rpeak):int(rpeaks[index+1])]
            epoch_after = epoch_after[0:int(len(epoch_after)/2)]

            s_wave_index = np.min(find_peaks(epoch_after)[0])
            s_wave = rpeak + s_wave_index
            t_wave_index = s_wave_index + np.argmax(epoch_after[s_wave_index:])
            t_wave = rpeak + t_wave_index

            inter_st = epoch_after[s_wave_index:t_wave_index]
            inter_st_derivative = np.gradient(inter_st, 2)
            t_start_index = nk.find_closest_in_list(len(inter_st_derivative)/2, find_peaks(inter_st_derivative)[0])
            t_start = s_wave + t_start_index
            t_end = np.min(find_peaks(epoch_after[t_wave_index:])[0])
            t_end = t_wave + t_end

            s_waves.append(s_wave)
            t_waves.append(t_wave)
            t_waves_starts.append(t_start)
            t_waves_ends.append(t_end)
        except ValueError:
            pass
        except IndexError:
            pass
    ecg_waves = {"T_Waves": t_waves,
                 "P_Waves": p_waves,
                 "Q_Waves": q_waves,
                 "S_Waves": s_waves,
                 "Q_Waves_Onsets": q_waves_starts,
                 "T_Waves_Onsets": t_waves_starts,
                 "T_Waves_Ends": t_waves_ends}
    return(ecg_waves)

rpeaks = ecg_find_peaks(records[0]['i']['singal'])
detect = ecg_wave_detector(records[0]['i']['singal'], rpeaks)

rpeaks

detect

"""원래 : 

array([ 641,  664,  690,  773,  840,  887, 1252, 1282, 1301, 1324, 1344,
       1374, 1457, 1519, 1567, 1911, 1938, 1961, 1980, 2002, 2028, 2118,
       2176, 2219, 2538, 2581, 2604, 2624, 2645, 2670, 2758, 2820, 2864,
       3224, 3252, 3278, 3297, 3316, 3340, 3434, 3491, 3534, 3882, 3908,
       3937, 3953, 3971, 3996])
"""

xpos = list(range(0, 5000))

pyplot.rcParams["font.size"] = 20
pyplot.rcParams["figure.figsize"] = (20, 10)
pyplot.figure()
pyplot.legend()
pyplot.grid()
pyplot.title('id:1 , signal Time Series')
pyplot.xlabel('10Seconds with 500Hz')
pyplot.ylabel('signal')
plt.plot(xpos, signal_1)
plt.scatter(detect['Q_Waves_Onsets'],signal_1[detect['Q_Waves_Onsets']],c='r' )
plt.scatter(rpeaks,signal_1[rpeaks],c='y' )
plt.scatter(detect['S_Waves'],signal_1[detect['S_Waves']],c='g' )

plt.show()

"""파형분할 전처리

성능평가(T ONSET, P ONSET)_detect한 점들에 대해서는 잘 맞추는데, detect한 점 수 자체가 적어서 정확도가 낮게 나오는듯 ㅠ
"""

rpeaks

detect

records[0]['i']['anno_idx']

len(records[0]['i']['anno'])

#q-onset
q_onset = [] #실제 q onset점 
for i in range(0,48,9):
  q_onset.append(records[0]['i']['anno_idx'][i])

q_onset

detect['Q_Waves_Onsets']

TP = 0
for i in detect['Q_Waves_Onsets']:
  for k in q_onset:
    if (i >= k-75 and i <= k + 75): #75인 이유 : 1초당 500개 라 0.15초(150ms) 당 75개라 +- 75 안에 있으면 맞추었다 판단..이게 맞나?
      TP = TP+1
FP = len(q_onset) - TP

FN = 0
for i in q_onset:
  for k in detect['Q_Waves_Onsets'] :
    if (i >= k-75 and i <= k + 75):
      FN = FN+1

SE = TP/(TP + FN)
PPV = TP/(TP + FP)

SE

PPV

#T-onset
t_onset = [] #실제 t_onset점
for i in range(3,48,9):
  t_onset.append(records[0]['i']['anno_idx'][i])

t_onset

detect['T_Waves_Onsets']

TP = 0
for i in detect['T_Waves_Onsets']:
  for k in t_onset:
    if (i >= k-75 and i <= k + 75):
      TP = TP+1
FP = len(detect['T_Waves_Onsets']) - TP

TP

FN = 0
for i in t_onset:
  for k in detect['T_Waves_Onsets'] :
    if (i >= k-75 and i <= k + 75):
      FN = FN+1

SE = TP/(TP + FN)
PPV = TP/(TP + FP)

SE

PPV

"""12개 리드 + 200명에 대한 성능평가....

"""