import re

with open("d:/git-repo/obs-sei-stamper/src/sei-handler.c", "r", encoding="utf-8") as f:
    content = f.read()

# Completely replace build_sei_nal_unit
new_build_sei = """bool build_sei_nal_unit(const uint8_t *payload, size_t payload_size,
                        sei_nal_type_t nal_type, uint8_t **nal_unit_out,
                        size_t *nal_unit_size) {
  if (!payload || !nal_unit_out || !nal_unit_size) {
    sei_log(LOG_ERROR, "Invalid parameters for build_sei_nal_unit");
    return false;
  }

  size_t header_size = (nal_type == SEI_NAL_H264) ? 1 : 2;
  uint8_t type_buf[10];
  uint8_t size_buf[10];

  size_t type_len = write_variable_length(type_buf, SEI_TYPE_USER_DATA_UNREGISTERED);
  size_t size_len = write_variable_length(size_buf, payload_size); // MUST be unescaped size!

  // 1. Build the RBSP (Raw Byte Sequence Payload)
  size_t rbsp_size = type_len + size_len + payload_size + 1;
  uint8_t *rbsp = (uint8_t *)bmalloc(rbsp_size);
  if (!rbsp) return false;

  size_t roffset = 0;
  memcpy(rbsp + roffset, type_buf, type_len); roffset += type_len;
  memcpy(rbsp + roffset, size_buf, size_len); roffset += size_len;
  memcpy(rbsp + roffset, payload, payload_size); roffset += payload_size;
  rbsp[roffset++] = 0x80; // RBSP trailing bits

  // 2. Apply Emulation Prevention Bytes (EPB) to the RBSP
  // Worst case: every byte turns into 2 bytes
  uint8_t *escaped_rbsp = (uint8_t *)bmalloc(rbsp_size * 2);
  if (!escaped_rbsp) {
    bfree(rbsp);
    return false;
  }

  size_t escaped_size = 0;
  int zero_count = 0;
  for (size_t i = 0; i < rbsp_size; i++) {
    if (zero_count == 2 && rbsp[i] <= 3) {
      escaped_rbsp[escaped_size++] = 0x03;
      zero_count = 0;
    }
    if (rbsp[i] == 0) zero_count++;
    else zero_count = 0;
    
    escaped_rbsp[escaped_size++] = rbsp[i];
  }

  // 3. Construct final NAL unit
  size_t total_size = 4 + header_size + escaped_size;
  uint8_t *nal_unit = (uint8_t *)bmalloc(total_size);
  if (!nal_unit) {
    bfree(rbsp);
    bfree(escaped_rbsp);
    return false;
  }

  size_t offset = 0;
  // Start Code
  nal_unit[offset++] = 0x00;
  nal_unit[offset++] = 0x00;
  nal_unit[offset++] = 0x00;
  nal_unit[offset++] = 0x01;

  // NAL Header
  if (nal_type == SEI_NAL_H264) {
    nal_unit[offset++] = (0 << 7) | (0 << 5) | SEI_NAL_H264;
  } else {
    nal_unit[offset++] = (0 << 7) | (nal_type << 1) | 0;
    nal_unit[offset++] = (0 << 5) | 1;
  }

  // Append Escaped RBSP
  memcpy(nal_unit + offset, escaped_rbsp, escaped_size);
  offset += escaped_size;

  *nal_unit_out = nal_unit;
  *nal_unit_size = offset;

  bfree(rbsp);
  bfree(escaped_rbsp);

  sei_log(LOG_DEBUG, "Built SEI NAL unit (%zu bytes)", offset);
  return true;
}"""

content = re.sub(
    r"bool build_sei_nal_unit\(const uint8_t \*payload, size_t payload_size,[\s\S]*?return true;\n}",
    new_build_sei,
    content
)

# 4. Update extract_sei_payload size export
content = re.sub(
    r"\*payload_size = sei_size;\s*return true;",
    "*payload_size = data_rem - offset;\n        return true;",
    content
)

with open("d:/git-repo/obs-sei-stamper/src/sei-handler.c", "w", encoding="utf-8") as f:
    f.write(content)

