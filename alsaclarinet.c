#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <sys/eventfd.h>
#include <math.h>
#include <alsa/asoundlib.h>

int bufsize = 50000*2;

int16_t *buf=NULL;

snd_output_t *output = NULL;
snd_pcm_t *handle;
snd_pcm_sframes_t frames;
static char *device = "default";
#define SAMPLE_RATE 48000


int sync_fd1, sync_fd2;//see main()

void fill_buffer()
{	
	printf("%.8f\r\n", (2.0*(double)M_PI*(1.0/SAMPLE_RATE)));
	double theta=0.0;
	double freq=440.0;
	// dt = 1/SAMPLE_RATE
	// theta increment = freq*(2pi/SAMPLE_RATE), 1Hz takes SAMPLE_RATE cycles, freq Hz takes SAMPLE_RATE/freq cycles
	while(1)
	{
		uint64_t temp;		
		read(sync_fd1, &temp, 8);
		
		int loc;
		for(loc=0; loc<bufsize; loc++)
		{
			buf[loc] = 10000.0*sin(theta);
			theta+=freq*(2.0*(double)M_PI*(1.0/SAMPLE_RATE));
			// if(theta>(2.1*M_PI)) 
			// 	theta=0.0;
		}
		
		uint64_t unblock=(unsigned char)1;
		
		//unblock fill_buffer() thread
		again:
			if(write(sync_fd2, &unblock, 8) < 8)
			{
				goto again;
				printf("again lol\n");
			}
		
		
		printf("		filled\n");
	}
}


void write_buffer_audio()
{
	while(1)
	{
		uint64_t temp;		
		read(sync_fd2, &temp, 8);
		
		
		uint64_t unblock=(unsigned char)1;
		
		//unblock fill_buffer() thread
		again:
			if(write(sync_fd1, &unblock, 8) < 8)
			{
				goto again;
				printf("again lol\n");
			}
			
		frames = snd_pcm_writei(handle, buf, bufsize);
		if (frames < 0)
			frames = snd_pcm_recover(handle, frames, 0);
		if (frames < 0) 
		{
			printf("snd_pcm_writei failed: %s\n", snd_strerror(frames));
			break;
		}
		if (frames > 0 && frames < (long)bufsize)
			printf("Short write (expected %li, wrote %li)\n", (long)bufsize, frames);
		printf("written\n");
	}
}

void sched_realtime()
{
	struct sched_param sched;

	sched.sched_priority = 50;
	sched_setscheduler(0, SCHED_FIFO, &sched);
	sched_getparam(0, &sched);
}

int main(int argc, char *argv[])
{
	sched_realtime();
	
	buf = (uint16_t *)malloc(bufsize*sizeof(uint16_t));
	if(!buf)
	{
		printf("Couldnt allocate memory for buffer\n");
		exit(-2);
	}
		
	/*
	 * The eventfd(2) file descriptor for fill_buffer() to wait upon.
	 */
	sync_fd1 = eventfd(0, 0);
	sync_fd2 = eventfd(1, 0);
	
	if(sync_fd1 == -1 || sync_fd2 == -1)
	{
		fprintf(stderr, __FILE__ ": failed to open sync_fd\n");
		exit(0);
	}
	
	int err;


	/* 
	 * Create a new playback stream 
	 */
	if ((err = snd_pcm_open(&handle, device, SND_PCM_STREAM_PLAYBACK, 0) < 0))
	{
		fprintf(stderr, __FILE__ "Playback open error: %s\n", snd_strerror(err));
		exit(EXIT_FAILURE);
	}
	if ((err = snd_pcm_set_params(handle,
				SND_PCM_FORMAT_S16,
				SND_PCM_ACCESS_RW_INTERLEAVED,
				1,
				SAMPLE_RATE,
				1,
				50000)) < 0)
    {
		/* 0.5sec latency */
		printf("Playback open error: %s\n", snd_strerror(err));
        exit(EXIT_FAILURE);
    }
	
	
	pthread_t thread_fill, thread_write;
	
	pthread_create(&thread_fill, NULL, (void*) &fill_buffer, (void *)NULL);
	pthread_create(&thread_write, NULL, (void*) &write_buffer_audio, (void *)NULL);
	

	while(1){
		sleep(100000);
	}

	return 0;
}
