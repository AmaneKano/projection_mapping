int digitalPin = 2;
int val = LOW;
void setup() {
  // put your setup code here, to run once:
  pinMode(digitalPin, INPUT);
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  val = digitalRead(digitalPin);
  if(val==HIGH){
    Serial.print(val);
    Serial.print("\n");
    Serial.read();
    delay(100);
  }
}
