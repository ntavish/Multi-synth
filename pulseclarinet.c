#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <sys/eventfd.h>
#include <math.h>
#include <pulse/simple.h>
#include <pulse/error.h>

#define BUFSIZE 102400

short buf[BUFSIZE];

pa_simple *s = NULL;
int sync_fd;//see main()

void fill_buffer()
{	
	while(1)
	{
		unsigned char temp;	
		read(sync_fd, &temp, 1);
		ssize_t r=0;
		
		float theta=0.0;
		int loc;
		for(loc=0; loc<BUFSIZE; loc++)
		{
			buf[loc]=(short)(sin(theta)*(INT16_MAX/4));
			theta+=660*0.000142476;
			if(theta>2.*M_PI) 
				theta=0.0;
			r+=1;
		}
	}	
}


void write_buffer_audio()
{
	while(1)
	{
		uint8_t unblock=1;
		//unblock fill_buffer() thread
		write(sync_fd, &unblock, 1);
		
		int error;
		if (pa_simple_write(s, buf, (size_t)BUFSIZE, &error) < 0)
		{
			fprintf(stderr,
					__FILE__ ": pa_simple_write() failed: %s\n",
					pa_strerror(error));
		}
	}
}

void sched_realtime()
{
	struct sched_param sched;

	sched.sched_priority = 50;
	sched_setscheduler(0, SCHED_RR, &sched);
	sched_getparam(0, &sched);
}

int main(int argc, char *argv[])
{
	//sched_realtime();
	
	/* 
	 * The Sample format to use 
	 */

	
	static const pa_sample_spec ss = {
		.format = PA_SAMPLE_S16LE,
		.rate = 44100,
		.channels = 1
	};
	/*
	 * The eventfd(2) file descriptor for fill_buffer() to wait upon.
	 */
	sync_fd = eventfd(0, 0);
	
	if(sync_fd == -1)
	{
		fprintf(stderr, __FILE__ ": failed to open sync_fd\n");
		exit(0);
	}
	
	int ret = 1;
	int error;


	/* 
	 * Create a new playback stream 
	 */
	if (!(s = pa_simple_new(NULL, argv[0], PA_STREAM_PLAYBACK, NULL,
				"playback", &ss, NULL, NULL, &error)))
	{
		fprintf(stderr, __FILE__ ": pa_simple_new() failed: %s\n",
				pa_strerror(error));
		goto finish;
	}
	
	pthread_t thread_fill, thread_write;
	
	pthread_create(&thread_fill, NULL, (void*) &fill_buffer, (void *)NULL);
	pthread_create(&thread_write, NULL, (void*) &write_buffer_audio, (void *)NULL);

	
	/* 
	 * Make sure that every single sample was played 
	 */
	if (pa_simple_drain(s, &error) < 0)
	{
		fprintf(stderr, __FILE__ ": pa_simple_drain() failed: %s\n",
				pa_strerror(error));
		goto finish;
	}

	ret = 0;

  finish:

	if (s)
		pa_simple_free(s);

	return ret;
}
