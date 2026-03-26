import re

with open("d:/git-repo/obs-sei-stamper/src/sei-handler.c", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update build_sei_nal_unit to include EPB
epb_logic = """  /* Escape payload with Emulation Prevention Bytes (0x03) */
  uint8_t escaped_payload[2048];
  size_t escaped_size = 0;
  int zero_count = 0;
  for (size_t i = 0; i < payload_size; i++) {
    if (zero_count == 2 && payload[i] <= 3) {
      if (escaped_size < sizeof(escaped_payload)) escaped_payload[escaped_size++] = 0x03;
      zero_count = 0;
    }
    if (payload[i] == 0) {
      zero_count++;
    } else {
      zero_count = 0;
    }
    if (escaped_size < sizeof(escaped_payload)) escaped_payload[escaped_size++] = payload[i];
  }

  size_t type_len = write_variable_length(type_buf, SEI_TYPE_USER_DATA_UNREGISTERED);
  size_t size_len = write_variable_length(size_buf, escaped_size);

  size_t total_size = 4 + header_size + type_len + size_len + escaped_size + 1;"""

content = re.sub(
    r"\s*size_t type_len =\s*write_variable_length\(type_buf, SEI_TYPE_USER_DATA_UNREGISTERED\);\s*size_t size_len = write_variable_length\(size_buf, payload_size\);\s*size_t total_size = 4 \+ header_size \+ type_len \+ size_len \+ payload_size \+ 1;",
    epb_logic,
    content
)

content = re.sub(
    r"\s*/\* Payload \*/\s*memcpy\(nal_unit \+ offset, payload, payload_size\);\s*offset \+= payload_size;",
    "\n  /* Payload */\n  memcpy(nal_unit + offset, escaped_payload, escaped_size);\n  offset += escaped_size;",
    content
)

# 2. Update parse_ntp_sei to unescape EPB
unescape_logic = """bool parse_ntp_sei(const uint8_t *sei_data, size_t sei_size,
                   ntp_sei_data_t *ntp_data_out) {
  if (!sei_data || !ntp_data_out) {
    return false;
  }

  uint8_t unescaped[2048];
  size_t unescaped_size = 0;
  for (size_t i = 0; i < sei_size; i++) {
    if (i >= 2 && sei_data[i] == 0x03 && sei_data[i-1] == 0 && sei_data[i-2] == 0) {
      continue;
    }
    if (unescaped_size < sizeof(unescaped)) {
      unescaped[unescaped_size++] = sei_data[i];
    }
  }

  /* 查找我们的UUID */
  for (size_t i = 0; i + 32 <= unescaped_size; i++) {
    if (memcmp(unescaped + i, SEI_STAMPER_UUID, 16) == 0) {
      /* 找到了!解析数据 */
      size_t offset = i;

      /* UUID */
      memcpy(ntp_data_out->uuid, unescaped + offset, 16);
      offset += 16;

      /* PTS */
      int64_t pts = 0;
      pts |= ((int64_t)unescaped[offset++] << 56);
      pts |= ((int64_t)unescaped[offset++] << 48);
      pts |= ((int64_t)unescaped[offset++] << 40);
      pts |= ((int64_t)unescaped[offset++] << 32);
      pts |= ((int64_t)unescaped[offset++] << 24);
      pts |= ((int64_t)unescaped[offset++] << 16);
      pts |= ((int64_t)unescaped[offset++] << 8);
      pts |= (int64_t)unescaped[offset++];
      ntp_data_out->pts = pts;

      /* NTP seconds */
      uint32_t seconds = 0;
      seconds |= ((uint32_t)unescaped[offset++] << 24);
      seconds |= ((uint32_t)unescaped[offset++] << 16);
      seconds |= ((uint32_t)unescaped[offset++] << 8);
      seconds |= (uint32_t)unescaped[offset++];
      ntp_data_out->ntp_time.seconds = seconds;

      /* NTP fraction */
      uint32_t fraction = 0;
      fraction |= ((uint32_t)unescaped[offset++] << 24);
      fraction |= ((uint32_t)unescaped[offset++] << 16);
      fraction |= ((uint32_t)unescaped[offset++] << 8);
      fraction |= (uint32_t)unescaped[offset++];
      ntp_data_out->ntp_time.fraction = fraction;

      sei_log(LOG_DEBUG, "Parsed NTP SEI (PTS: %lld, NTP: %u.%u)", pts, seconds,
              fraction);

      return true;
    }
  }

  return false;
}"""

content = re.sub(
    r"bool parse_ntp_sei\(const uint8_t \*sei_data, size_t sei_size,[\s\S]*?return false;\n}",
    unescape_logic,
    content
)

# 3. Update extract_sei_payload to loop through NAL units
extract_logic = """static const uint8_t *find_start_code_sei(const uint8_t *data, size_t size, size_t *sc_size) {
  if (size < 3) return NULL;
  for (size_t i = 0; i < size - 2; i++) {
    if (data[i] == 0 && data[i+1] == 0) {
      if (data[i+2] == 1) {
        *sc_size = 3; return data + i;
      } else if (i < size - 3 && data[i+2] == 0 && data[i+3] == 1) {
        *sc_size = 4; return data + i;
      }
    }
  }
  return NULL;
}

bool extract_sei_payload(const uint8_t *nal_data, size_t nal_size,
                         const uint8_t **payload_out, size_t *payload_size) {
  if (!nal_data || !payload_out || !payload_size || nal_size < 5) {
    return false;
  }

  const uint8_t *current = nal_data;
  size_t remaining = nal_size;

  while (remaining > 0) {
    size_t sc_size = 0;
    const uint8_t *nal_start = find_start_code_sei(current, remaining, &sc_size);
    if (!nal_start) break;

    const uint8_t *data = nal_start + sc_size;
    size_t data_rem = remaining - (data - current);
    if (data_rem < 2) break; /* Need at least 2 bytes for H.265 header */

    uint8_t nal_type_byte = data[0];
    uint8_t nal_type = nal_type_byte & 0x1F;
    size_t offset = 0;
    bool is_sei = false;

    if (nal_type == SEI_NAL_H264) {
      is_sei = true;
      offset = 1;
    } else {
      uint8_t h265_type = (nal_type_byte >> 1) & 0x3F;
      if (h265_type == SEI_NAL_H265_PREFIX || h265_type == SEI_NAL_H265_SUFFIX) {
        is_sei = true;
        offset = 2;
      }
    }

    if (is_sei && data_rem > offset) {
      size_t sei_type;
      size_t type_read = read_variable_length(data + offset, data_rem - offset, &sei_type);
      offset += type_read;
      
      size_t sei_size;
      size_t size_read = read_variable_length(data + offset, data_rem - offset, &sei_size);
      offset += size_read;

      if (sei_type == SEI_TYPE_USER_DATA_UNREGISTERED && offset + sei_size <= data_rem) {
        *payload_out = data + offset;
        *payload_size = sei_size;
        return true;
      }
    }

    current = nal_start + 1; // Advance past current start code
    remaining = nal_size - (current - nal_data);
  }

  return false;
}"""

content = re.sub(
    r"bool extract_sei_payload\(const uint8_t \*nal_data, size_t nal_size,[\s\S]*?return true;\n}",
    extract_logic,
    content
)

with open("d:/git-repo/obs-sei-stamper/src/sei-handler.c", "w", encoding="utf-8") as f:
    f.write(content)
