int lockPin = 2;

void setup() {
  Serial.begin(115200);
  pinMode(lockPin, OUTPUT);
  digitalWrite(lockPin, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    String s = Serial.readStringUntil('\n');
    if (s.startsWith("elldetect")) {
      Serial.print("found\n");
    } else if (s.startsWith("open")) {
      digitalWrite(lockPin, HIGH);
      delay(1000);
      digitalWrite(lockPin, LOW);
      Serial.print("opened\n");
    }
  }
}
