#define _XOPEN_SOURCE 600
#include "platform.h"
#include <assert.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>
int main(void){
 int master=posix_openpt(O_RDWR|O_NOCTTY);assert(master>=0);
 assert(!grantpt(master)&&!unlockpt(master));
 int slave=open(ptsname(master),O_RDWR|O_NOCTTY);assert(slave>=0);
 struct termios raw;assert(!tcgetattr(slave,&raw));cfmakeraw(&raw);assert(!tcsetattr(slave,TCSANOW,&raw));
 assert(write(master,"JD\x26",3)==3);usleep(10000);
 struct jh_platform_serial serial;
 assert(!jh_platform_serial_adopt_format(&serial,slave,ptsname(master),9600,'O',2,1));
 assert(serial.pseudo_terminal && serial.stop_bits==2 && serial.baud==9600);
 unsigned char bytes[8];int n=jh_platform_serial_read(&serial,bytes,sizeof bytes,100);
 assert(n==3 && !memcmp(bytes,"JD\x26",3));
 assert(!tcgetattr(slave,&raw) && (raw.c_cflag&CSTOPB));
 jh_platform_serial_close(&serial);close(master);
 return 0;
}
