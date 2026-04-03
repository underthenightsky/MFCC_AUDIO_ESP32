# MFCC_AUDIO_ESP32
Cochlear implant with HIL worklow, sending PWM signals on specific word ouputs. ESP32 send the PWM signals in resposne to specific words it was trained on to mimic actual cochlear implant workflows where we cant send the word we think the audio signal matches but have to send analog signals instead. Python is used to calculate the MFCC response of a particular .wav file and send and plot the response using matplotlib.

![teminal_output](terminal_output.png)
![ouput](output.png)
