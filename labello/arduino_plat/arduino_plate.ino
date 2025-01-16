// Include the Arduino Stepper Library
#include <Stepper.h>

String buffer;

// Number of steps per output rotation
const int stepsPerRevolution = 200;

// Create Instance of Stepper library
Stepper myStepper(stepsPerRevolution, 8, 9, 10, 11);

void setup(){
  myStepper.setSpeed(2);
  char c;
  Serial.begin(9600);
  Serial.setTimeout(200);
  Serial.flush();
}

void loop(){
  while (!Serial.available());
  buffer = Serial.readString();
  if(buffer == "INIT") {
    Serial.println("INIT:DONE");
  }

  else if(buffer == "CHECK") {
    Serial.println("CKECK:DONE");
  }

  else{
    String cmd = buffer.substring(0,3);
    if (cmd == "ROT"){
      String val = buffer.substring(3);
      int steps = val.toInt();
      myStepper.step(-steps);
      Serial.println(cmd +  steps);
    }
  }

 // step one revolution in one direction:
 //  Serial.println("clockwise");
 // myStepper.step(stepsPerRevolution);
 // delay(500);

 // step one revolution in the other direction:
 // Serial.println("counterclockwise");
 //  myStepper.step(-stepsPerRevolution);
 // delay(500);
}