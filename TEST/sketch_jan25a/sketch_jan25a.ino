int blueSensorPin=A0;

void setup()
{Serial.begin(9600);
 pinMode(blueSensorPin, INPUT);
// pinMode(blueLEDPin, OUTPUT);
}
// Read phototransistor light levels, display raw and converted analog values.
// Produce varying intensity LED levels
void loop()
{
 int blueSensorValue = analogRead(blueSensorPin);
 delay(5);
 Serial.print("Raw Sensor value \t Blue:");
 Serial.println(blueSensorValue%1024*100);
 //delay(1000);
 //blueValue = blueSensorValue/4;
 
// Serial.print("Mapped Sensor Value \t Blue:");
// Serial.println(blueValue);
// //delay(1000);
// //analogWrite(blueLEDPin, blueValue);
// 
}
