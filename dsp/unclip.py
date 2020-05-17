import pdb
import numpy as np
import scipy.io.wavfile
import scipy.signal
import matplotlib.pyplot as plt
import wavio


# samp_rate, samples = sp.io.wavfile.read('../wavs/mono-32bit.wav', mmap=False)
my_wavio = wavio.read('../wavs/mono-32bit.wav')

samples = np.array(my_wavio.data)
samples = samples + (-1 * np.min(samples))
num_samples = len(samples)

# plt.plot(samples)
# clipped = scipy.signal.resample(samples, num_samples * 2)
clipped = np.copy(samples)
clipped = clipped/np.max(clipped)
clipped[clipped < 5e-19] = 0

# clipped = clipped[20000:20300]
# plt.plot(clipped)
# plt.ion()
# plt.show()

unclipped = np.zeros(clipped.shape)
start = False
i = 0
while i < len(clipped):
    if i < len(clipped) and clipped[i] > 0 or not start:
        unclipped[i] = clipped[i]
        i += 1
        if(i < len(clipped) and clipped[i] > 0):
            start = True
        continue
    else:
        # pdb.set_trace()
        mirror_begin = i
        mirror_i = 0
        mirror = -clipped[mirror_begin - mirror_i]
        unclipped[i] = mirror
        mirror_i +=1
        mirror = -clipped[mirror_begin - mirror_i]
        i+=1
        while i < len(clipped) and mirror < 0 and clipped[i] <= 0:
            unclipped[i] = mirror
            mirror_i +=1
            mirror = -clipped[mirror_begin - mirror_i]
            i+=1



# for sample_i, sample in enumerate(clipped):
    # if sample == 0 and sample_i > 0:
        # clipped[sample_i] = clipped[sample_i - 1] * -1

fig, ax = plt.subplots(1,2)
ax[0].plot(clipped)
ax[1].plot(unclipped)

plt.show()

wavio.write("unclipped.wav", unclipped, my_wavio.rate, sampwidth=3) 

