#if defined(ARDUINO) && ARDUINO >= 100
#include "Arduino.h"
#else
#include "WProgram.h"
#endif

#include "EMGFilters.h"
#include "math.h"

#define TIMING_DEBUG 1

#define SensorInputPinA A0 // input pin number
#define SensorInputPinB A1 // input pin number
#define SensorInputPinC A2 // input pin number

EMGFilters filterA;
EMGFilters filterB;
EMGFilters filterC;
// discrete filters must works with fixed sample frequence
// our emg filter only support "SAMPLE_FREQ_500HZ" or "SAMPLE_FREQ_1000HZ"
// other sampleRate inputs will bypass all the EMG_FILTER
int sampleRate = SAMPLE_FREQ_500HZ;
// For countries where power transmission is at 50 Hz
// For countries where power transmission is at 60 Hz, need to change to
// "NOTCH_FREQ_60HZ"
// our emg filter only support 50Hz and 60Hz input
// other inputs will bypass all the EMG_FILTER
int humFreq = NOTCH_FREQ_60HZ;

// Calibration:
// put on the sensors, and release your muscles;
// wait a few seconds, and select the max value as the threshold;
// any value under threshold will be set to zero
static int Threshold = pow(10, 2);

unsigned long timeStamp;
unsigned long timeBudget;
unsigned long initTime;
double output;

void setup() {
    /* add setup code here */
    filterA.init(sampleRate, humFreq, true, true, true);
    filterB.init(sampleRate, humFreq, true, true, true);
    filterC.init(sampleRate, humFreq, true, true, true);

    // open serial
    Serial.begin(115200);

    // setup for time cost measure
    // using micros()
    timeBudget = 1e6 / sampleRate;
    // micros will overflow and auto return to zero every 70 minutes
}

void loop() {
    /* add main program code here */
    // In order to make sure the ADC sample frequence on arduino,
    // the time cost should be measured each loop
    /*------------start here-------------------*/
    timeStamp = micros();
    int ValueA = analogRead(SensorInputPinA);
    int ValueB = analogRead(SensorInputPinB);
    int ValueC = analogRead(SensorInputPinC);

    // filter processing
    int DataAfterFilterA = filterA.update(ValueA);
    int DataAfterFilterB = filterB.update(ValueB);
    int DataAfterFilterC = filterC.update(ValueC);
    
    // // any value under threshold will be set to zero
    DataAfterFilterA = (pow(DataAfterFilterA, 2) > Threshold) ? DataAfterFilterA : 0;
    DataAfterFilterB = (pow(DataAfterFilterB, 2) > Threshold) ? DataAfterFilterB : 0;
    DataAfterFilterC = (pow(DataAfterFilterC, 2) > Threshold) ? DataAfterFilterC : 0;

    //timeStamp = micros() - timeStamp;
    if (TIMING_DEBUG) {
        // Serial.print("Read Data: "); Serial.println(Value);
        // Serial.print("Filtered Data: ");Serial.println(DataAfterFilter);
        // Serial.print("Squared Data: ");
        Serial.print(DataAfterFilterA);
        Serial.print(",");
        Serial.print(DataAfterFilterB);
        Serial.print(",");
        Serial.println(DataAfterFilterC);
        //Serial.print("Filters cost time: "); Serial.println(timeStamp);
        // the filter cost average around 520 us
    }

    /*------------end here---------------------*/
    // if less than timeBudget, then you still have (timeBudget - timeStamp) to
    // do your work
    //delayMicroseconds(200);
    // if more than timeBudget, the sample rate need to reduce to
    // SAMPLE_FREQ_500HZ
}
