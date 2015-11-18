#include <avr/io.h>

#define LED_PIN 13

///////////////////////////////////////////////
void adc_init(void)
{
 ADMUX = _BV(REFS0); // AVCC with external cap
           
 ADCSRA = _BV(ADEN) |
          _BV(ADPS2) | _BV(ADPS1) | _BV(ADPS0); 
}
/*
inline void adc_set_channel(uint8_t channel) {
  ADMUX = (ADMUX & ~(0b00000111)) | (channel & 0x07);
}

inline uint16_t adc_read_16bit(void) {
  ADCSRA |= _BV(ADSC);
  while (ADCSRA & _BV(ADSC)) {
  }
  return ADC;
}

uint16_t adc_read_10bit(uint8_t channel) {
   adc_set_channel(channel);
   return adc_read_16bit();
}
*/
///////////////////////////////////////////////
void timer1_init(void) {
  TCCR1A = 0;   
  TCCR1B = _BV(WGM12) |  // turn on CTC mode with OCR1A
           _BV(CS11) | _BV(CS10);    // /64 prescaler (62500 Hz Clock)
  
  OCR1A = 249;// = (16*10^6 Hz / (1 * 64)) / (1000 Hz) - 1
}

const double one_mili_sec = 1; // one count per milisecond (multiply by milisec time to get required counts)

void timer1_wait_for_int(void) {
  while (!(TIFR1 & _BV(OCF1A)));
  TIFR1 |= _BV(OCF1A);
}

///////////////////////////////////////////////
void setup() {
  // put your setup code here, to run once:
  adc_init();
 
  timer1_init();
  
  pinMode(LED_PIN, OUTPUT);
  
  Serial.begin(115200); 
  flush_incoming_serial();

 // uart_setup();
}

void flush_incoming_serial(void) {
    while (Serial.available() > 0)
      Serial.read();
}

void read_and_send_adc(void) {
//    uint8_t val = adc_read_8bit();
//    Serial.write(val);

  uint16_t val1 = analogRead(0); // adc_read_10bit(0);
  uint16_t val2 = analogRead(1); //adc_read_10bit(1);

  uint8_t byte1 = 0x80 | (val1 & 0x7f);
  uint8_t byte2 = 0x80 | (val1 >> 7) | ((val2 & 0x0f) << 3);
  uint8_t byte3 = val2 >> 4;
  
  Serial.write(byte3);
  Serial.write(byte2);
  Serial.write(byte1);
}

void loop() {
  // put your main code here, to run repeatedly:

  digitalWrite(LED_PIN, 0);

  for (uint16_t i=0; i<32;i++) {
   Serial.write('S');
  }
  
  // wait for incoming serial
  while (Serial.read() != 's');

  // empty buffer
  flush_incoming_serial();
  
  while(true) { 
    timer1_wait_for_int();
    
    read_and_send_adc();
      
    // reset code
    if (Serial.available() != 0) {
      if (Serial.read() == 'r')
        return;
    }
  }
}
