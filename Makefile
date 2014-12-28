CC=gcc

alsaclarinet: alsaclarinet.c
	$(CC) alsaclarinet.c -o alsaclarinet -lm -lpthread `pkg-config --cflags --libs alsa`
