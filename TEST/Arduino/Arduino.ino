#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT22

DHT dht(DHTPIN,DHTTYPE);

int chk;
float hum;
float temp;

void setup(){
  Serial.begin(9600);
  dht.begin();
}


void loop(){
  hum=dht.readHumidity();
  temp=dht.readTemperature();
  Serial.print(floor(temp));
  Serial.print(" ");
  Serial.println(floor(hum));
  delay(2000);
}
