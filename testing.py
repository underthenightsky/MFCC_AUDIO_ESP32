import serial
import struct
import time
import librosa
import numpy as np
import matplotlib.pyplot as plt
import sys

# --- CONFIGURATION ---
PORT = 'COM3'         
BAUD_RATE = 115200
SAMPLE_RATE = 16000
DURATION = 1          
N_MFCC = 13

# --- HARDWARE SIMULATION PARAMS ---
MAX_VOLTAGE = 3.3     # ESP32 operates at 3.3V
TAU = 0.05            # RC Time Constant (Controls how fast the simulated capacitor charges)
SIM_TIME = 0.5        # Simulate 500ms of oscilloscope time

def extract_mfcc(file_path):
    print(f"Extracting MFCCs from {file_path}...")
    audio, _ = librosa.load(file_path, sr=SAMPLE_RATE, duration=DURATION)
    if len(audio) < SAMPLE_RATE:
        audio = np.pad(audio, (0, SAMPLE_RATE - len(audio)), 'constant')
    mfccs = librosa.feature.mfcc(y=audio, sr=SAMPLE_RATE, n_mfcc=N_MFCC, hop_length=512, n_fft=1024)
    return mfccs.T.flatten()

def simulate_oscilloscope(predicted_class):
    print(f"Simulating oscilloscope trace for class: {predicted_class}")
    
    # Map the class to a target PWM duty cycle / analog voltage
    if "yes" in predicted_class:
        target_v = MAX_VOLTAGE * 0.25
    elif "no" in predicted_class:
        target_v = MAX_VOLTAGE * 0.50
    elif "up" in predicted_class:
        target_v = MAX_VOLTAGE * 0.75
    else:
        target_v = MAX_VOLTAGE * 0.05 # Idle noise

    # Generate time axis
    t = np.linspace(0, SIM_TIME, 500)
    
    # Calculate the simulated RC filter capacitor charge curve
    # V_c(t) = V_in * (1 - e^(-t / RC))
    voltage_curve = target_v * (1 - np.exp(-t / TAU))
    
    # Add a tiny bit of simulated electrical noise for realism
    noise = np.random.normal(0, 0.02, voltage_curve.shape)
    voltage_curve += noise

    # Plot the results
    plt.figure(figsize=(10, 5))
    plt.plot(t, voltage_curve, color='cyan', linewidth=2, label="Simulated Electrode Voltage")
    plt.axhline(y=target_v, color='red', linestyle='--', alpha=0.5, label="Target Voltage")
    
    # Styling the plot to look like an oscilloscope screen
    plt.title(f'Virtual Oscilloscope: Cochlear Stimulation for "{predicted_class.strip()}"')
    plt.xlabel('Time (Seconds)')
    plt.ylabel('Amplitude (Volts)')
    plt.ylim(0, 3.5)
    plt.grid(color='green', linestyle=':', linewidth=0.5)
    plt.gca().set_facecolor('black')
    plt.legend()
    plt.tight_layout()
    plt.show()

def run_closed_loop_test(mfcc_data, port, baud_rate):
    try:
        with serial.Serial(port, baud_rate, timeout=3) as ser:
            time.sleep(2)
            while ser.in_waiting:
                ser.readline() # Clear startup junk

            print("Sending features to ESP32...")
            byte_data = struct.pack(f'<{len(mfcc_data)}f', *mfcc_data)
            ser.write(byte_data)
            
            time.sleep(0.5) 
            
            while ser.in_waiting:
                response = ser.readline().decode('utf-8').strip()
                if "Predicted" in response:
                    print(f"ESP32 Output: {response}")
                    
                    # Parse the predicted label from the string (e.g., "Predicted: yes (0.95)...")
                    # Assuming format: Predicted: label (prob) | ...
                    parts = response.split(' ')
                    if len(parts) > 1:
                        predicted_label = parts[1]
                        simulate_oscilloscope(predicted_label)
                    
    except serial.SerialException as e:
        print(f"Serial Error: {e}")

if __name__ == "__main__":
    test_audio_file = "yes.wav" # Ensure this file exists in your directory
    try:
        mfcc_features = extract_mfcc(test_audio_file)
        run_closed_loop_test(mfcc_features, PORT, BAUD_RATE)
    except Exception as e:
        print(f"Error: {e}")