#include <MFCC_AUDIO_ESP32_inferencing.h>

float input_buffer[EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE];

// --- Hardware Simulation Configuration ---
const int ELECTRODE_PIN = 18; // Connect your oscilloscope/LED here

void setup() {
    Serial.setRxBufferSize(2048); 
    Serial.begin(115200);
    while (!Serial);
    
    // Configure the PWM pin (Using standard Arduino API supported by newer ESP32 cores)
    // If you are using an older ESP32 core, you might need the ledcSetup() functions instead.
    pinMode(ELECTRODE_PIN, OUTPUT);
    analogWrite(ELECTRODE_PIN, 0); 
    
    Serial.println("Edge Impulse Inferencing & Hardware Simulation Ready.");
}

void loop() {
    if (Serial.available() >= sizeof(input_buffer)) {
        
        Serial.readBytes((char*)input_buffer, sizeof(input_buffer));

        signal_t signal;
        int err = numpy::signal_from_buffer(input_buffer, EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE, &signal);
        if (err != 0) return;

        ei_impulse_result_t result = { 0 };
        EI_IMPULSE_ERROR res = run_classifier(&signal, &result, false);
        if (res != EI_IMPULSE_OK) return;

        int best_idx = 0;
        float best_val = 0.0;
        
        for (size_t ix = 0; ix < EI_CLASSIFIER_LABEL_COUNT; ix++) {
            if (result.classification[ix].value > best_val) {
                best_val = result.classification[ix].value;
                best_idx = ix;
            }
        }
        
        Serial.printf("Predicted: %s (%.2f) | DSP: %dms | Inf: %dms\n", 
                      result.classification[best_idx].label, best_val, 
                      result.timing.dsp, result.timing.classification);
                      
        // --- SIMULATE THE COCHLEAR IMPLANT STIMULATION ---
        // Map the predicted class to a specific electrical output (0-255 duty cycle)
        // Adjust "class_name" to match the actual labels in your Edge Impulse project
        
        String predicted_label = String(result.classification[best_idx].label);
        // just give signals with varying duty cycles instead of just outputting the word output
        // as cochlear implants work on electronic signals such as these not sending word
        //responses for each sound signal
        if (predicted_label == "yes") {
            analogWrite(ELECTRODE_PIN, 64);  // 25% Duty Cycle
        } 
        else if (predicted_label == "no") {
            analogWrite(ELECTRODE_PIN, 128); // 50% Duty Cycle
        } 
        else if (predicted_label == "up") {
            analogWrite(ELECTRODE_PIN, 192); // 75% Duty Cycle
        }
        else {
            analogWrite(ELECTRODE_PIN, 10);  // Idle / Low stimulation
        }
    }
}