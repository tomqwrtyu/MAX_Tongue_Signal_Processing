#include <string.h>
#define EMG_PIN A0

int light = 13;
int readTime = 0;
double sum = 0.0;

void setup()
{
  pinMode(EMG_PIN, INPUT);
  pinMode(light, OUTPUT);
  Serial.begin(9600);
}
void loop()
{
  float temp = analogRead(EMG_PIN);
  readTime++;
  sum += temp;
  String output = "" + String(temp / readTime);
  Serial.println(temp);
  if (Serial.available())
  {
    char mode = Serial.read();
    if (mode == '1')
    {
      digitalWrite(light, HIGH);
    }
    else
    {
      digitalWrite(light, LOW);
    }
  }
  delay(10);
}
