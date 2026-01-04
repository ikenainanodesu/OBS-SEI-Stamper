#ifndef NVENC_ENCODER_H
#define NVENC_ENCODER_H

#include <obs-module.h>

#ifdef ENABLE_NVENC

#include "ntp-client.h"
#include <libavcodec/avcodec.h>
#include <libavutil/opt.h>

typedef struct nvenc_encoder {
  obs_encoder_t *encoder;

  /* FFmpeg 编码器 */
  const AVCodec *codec;
  AVCodecContext *codec_context;
  AVFrame *frame;
  AVPacket *packet;

  /* 配置 */
  int width;
  int height;
  int fps_num;
  int fps_den;
  int bitrate; // kbps
  int keyint;  // frames
  int bframes;
  char *profile;
  char *preset;

  /* Extra Data (SPS/PPS) */
  uint8_t *extra_data;
  size_t extra_data_size;

  /* NTP 同步 */
  struct ntp_client ntp_client;
  uint64_t last_ntp_sync_time;
  ntp_timestamp_t current_ntp_time;
  bool ntp_enabled;
  uint32_t ntp_sync_interval_ms; /* NTP同步间隔（毫秒） */

  /* Packet 缓冲区 */
  uint8_t *packet_buffer;
  size_t packet_buffer_size;

} nvenc_encoder_t;

bool nvenc_encoder_init(nvenc_encoder_t *enc, obs_data_t *settings,
                        video_t *video);
void nvenc_encoder_destroy(nvenc_encoder_t *enc);
bool nvenc_encoder_encode(nvenc_encoder_t *enc, struct encoder_frame *frame,
                          struct encoder_packet *packet, bool *received_packet);
void nvenc_encoder_get_defaults(obs_data_t *settings);
obs_properties_t *nvenc_encoder_properties(void *unused);
bool nvenc_encoder_extra_data(void *data, uint8_t **extra_data, size_t *size);
void nvenc_encoder_video_info(void *data, struct video_scale_info *info);

extern struct obs_encoder_info nvenc_encoder_info;

#endif // ENABLE_NVENC

#endif // NVENC_ENCODER_H
