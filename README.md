# OBS SEI Stamper Plugin

<img src="pic\sei_stamper_gau.png" alt="isolated" width="250"/>


**Frame-Level Video Synchronization for OBS Studio**

[English](#english) | [中文](README.chs.md) | [日本語](README.jpn.md)

---

## English

### Overview

OBS SEI Stamper is an OBS Studio plugin that enables **frame-level video synchronization** across multiple streams by embedding NTP timestamps into video streams using SEI (Supplemental Enhancement Information).

**Key Features:**
- 🎯 **Frame-accurate synchronization** using NTP timestamps
- 📡 **Multiple hardware encoders**: Intel QuickSync, NVIDIA NVENC, AMD AMF
- 🚀 **GPU acceleration**: Hardware-accelerated H.264 encoding with SEI support
- 🔄 **Sender & Receiver**: Complete solution for encoding and decoding
- 🌐 **SRT streaming**: Built-in SRT receiver for low-latency streaming
- ⏱️ **Microsecond precision**: NTP-based timing for professional applications

### Use Cases

- Multi-camera live production synchronization
- Remote studio frame-level sync
- Broadcast-quality multi-source alignment
- Live concert/event multi-angle recording

### Demo Video

📺 **[Watch Demo Video on YouTube](https://youtu.be/9aJCHxzy-ME)** *(Chinese language)*

This demonstration shows OBS sending 4 SRT streams with identical settings over a local network. Using native OBS Media Source cannot achieve synchronization between streams, but with this plugin, all 4 streams are synchronized to within ±1 frame accuracy.

---

## Installation

### Quick Install (Recommended)

Download the latest release from [Releases](https://github.com/yourusername/obs-sei-stamper/releases) page.

The release package includes:
- `obs-sei-stamper.dll` - Main plugin
- `srt.dll` - SRT library for receiver functionality
- Locale files for multi-language support

### Prerequisites

- OBS Studio 28.0 or later
- Windows 10/11 (64-bit)

### Manual Install Steps

1. **Download the release package** from the [Releases](https://github.com/yourusername/obs-sei-stamper/releases) page

2. **Copy to OBS plugins directory:**
   ```powershell
   # Copy plugin DLL
   Copy-Item obs-sei-stamper.dll "C:\Program Files\obs-studio\obs-plugins\64bit\"
   
   # Copy SRT library
   Copy-Item srt.dll "C:\Program Files\obs-studio\obs-plugins\64bit\"
   ```

3. **Copy locale files:**
   ```powershell
   # Create directory
   New-Item -ItemType Directory -Force `
       "C:\Program Files\obs-studio\data\obs-plugins\obs-sei-stamper\locale"
   
   # Copy locale files
   Copy-Item data\locale\* `
       "C:\Program Files\obs-studio\data\obs-plugins\obs-sei-stamper\locale\" -Recurse
   ```

4. **Restart OBS Studio**

---

## Usage

### Sender (Encoder)

1. Open **Settings → Output → Output Mode: Advanced**
2. Select a SEI Stamper encoder:
   - **SEI Stamper (Intel QuickSync)** - For Intel integrated/Arc GPUs
   - **SEI Stamper (NVIDIA NVENC)** - For NVIDIA GPUs
   - **SEI Stamper (AMD AMF)** - For AMD GPUs
3. Configure encoder properties:
   - **NTP Server**: `time.windows.com` (or your preferred NTP server)
   - **NTP Port**: `123` (default)
   - **Enable NTP Sync**: ✓
4. Start streaming/recording

The encoder will automatically insert NTP timestamps into every frame using SEI metadata.

### Receiver (Source)

1. In your OBS scene, click **Add Source +**
2. Select **SEI Receiver**
3. Configure the source:
   - **SRT URL**: `srt://sender-ip:port` (e.g., `srt://192.168.1.100:9000`)
   - **Enable NTP Synchronization**: ✓
   - **NTP Server**: Same as sender
4. Click **OK**

The receiver will:
- Connect to the SRT stream
- Decode video frames
- Extract NTP timestamps from SEI
- Intelligently synchronize playback using adaptive NTP sync

> **⚠️ Important**: The encoder and receiver **must use the same NTP server** for accurate synchronization.

---

## Verification

### Check SEI Data with FFprobe

```powershell
# View frame information
ffprobe -select_streams v:0 -show_frames output.mp4 2>&1 | Select-String "SEI"

# Detailed frame data
ffprobe -select_streams v:0 -show_frames -show_entries frame=pict_type output.mp4
```

### Check with MediaInfo

```powershell
MediaInfo --Full output.mp4 | Select-String "SEI"
```

---

## Technical Details

### Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Sender    │         │  SRT Stream  │         │  Receiver   │
│  (Encoder)  │────────▶│   + SEI      │────────▶│  (Source)   │
└─────────────┘         └──────────────┘         └─────────────┘
      │                                                  │
      ▼                                                  ▼
┌─────────────┐                                  ┌─────────────┐
│ NTP Client  │◀─────────────────────────────────▶│ NTP Client  │
└─────────────┘         NTP Server               └─────────────┘
```

### SEI Format

- **UUID**: Custom identifier (`a5b3c2d1-e4f5-6789-abcd-ef0123456789`)
- **Payload Type**: User Data Unregistered (Type 5)
- **Data Structure**:
  - UUID (16 bytes)
  - PTS (8 bytes)
  - NTP Timestamp (8 bytes: 4 bytes seconds + 4 bytes fraction)

### NTP Synchronization Strategy

#### Encoder (Sender)
- **Sync Interval**: Every 60 seconds
- **Trigger**: Automatic periodic sync during encoding
- **Purpose**: Ensure encoder's NTP time remains accurate

#### Receiver (Source)
- **Intelligent Sync**: Adaptive synchronization using two triggers
  1. **Keyframe Trigger**: Syncs on keyframes (IDR) with **minimum 10-second interval**
  2. **Drift Detection**: Syncs when time drift exceeds configured threshold (default 50ms)
- **Purpose**: Maintain high precision while minimizing network overhead
- **Performance**: Minimum sync interval prevents excessive NTP requests

**Workflow**:
```
Receive Frame with SEI
   ↓
Is Keyframe + 10s passed? ──Yes──► Trigger NTP Sync
   ↓ No
Time Drift > Threshold? ──Yes──► Trigger NTP Sync
   ↓ No
Use Existing NTP Time
```

### NTP Configuration Recommendations

#### Encoder Settings

| Parameter | Range | Default | Recommended |
|-----------|-------|---------|-------------|
| NTP Sync Interval | 1-600s | 60s | **30-120s** |

**Usage Scenarios**:
- **High Precision**: 10-30s (more frequent sync, higher accuracy)
- **Standard**: 60s (balanced, recommended for most cases)
- **Resource Limited**: 120-300s (reduce NTP server load)

#### Receiver Settings

| Parameter | Range | Default | Recommended |
|-----------|-------|---------|-------------|
| NTP Drift Threshold | 10-1000ms | 50ms | **30-100ms** |
| NTP Sync Interval | 100ms-1h | 10s | **10-60s** |

**Usage Scenarios**:
- **Strict Sync**: Drift 20-30ms, Interval 5-10s
- **Standard**: Drift 50ms, Interval 10-60s (Default)
- **Relaxed**: Drift 100ms, Interval 120s+ (Network saving)

> **ℹ️ Note**: The synchronization interval is now fully configurable. A minimum interval is enforced by your setting (default 10s) to prevent performance issues. You can lower this value if your network and CPU can handle frequent NTP requests.

### Supported Encoders

| Encoder | Hardware | SEI NAL Type | Min. Version | Status |
|---------|----------|--------------|--------------|--------|
| SEI Stamper (Intel QuickSync) | Intel iGPU/Arc | Type 6 | v1.0.0 | ✅ |
| SEI Stamper (NVIDIA NVENC) | NVIDIA GPU | Type 6 | v1.1.0 | ✅ |
| SEI Stamper (AMD AMF) | AMD GPU | Type 6 | v1.1.0 | ✅ |

---

## Building from Source

### Requirements

- **CMake** 3.20 or later
- **Visual Studio 2022** (with C++ Desktop Development workload)
- **OBS Studio source code** (included as dependency)
- **FFmpeg libraries** (provided by OBS)
- **libsrt** (included in repository)

### Quick Build (Recommended)

For users without build experience, use the automated build script:

1. **Run the build script:**
   ```powershell
   # Navigate to project directory
   cd obs-sei-stamper
   
   # Run the automated build script
   .\build_and_install.bat
   ```

2. **Get the plugin:**
   - After successful build, plugin files will be in `out/obs-studio/` directory
   - Plugin structure mirrors OBS installation directory

3. **Install:**
   - Copy contents of `out/obs-studio/` to your OBS installation directory
   - Default location: `C:\Program Files\obs-studio`
   - **Administrator privileges required**

### Manual Build Steps

If you prefer manual control over the build process:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/obs-sei-stamper.git
   cd obs-sei-stamper
   ```

2. **Configure CMake:**
   ```powershell
   mkdir build
   cd build
   cmake .. -G "Visual Studio 17 2022" -A x64
   ```

3. **Build:**
   ```powershell
   cmake --build . --config Release
   ```

4. **Install (optional):**
   ```powershell
   cmake --install . --config Release
   ```

5. **Output files:**
   - Plugin: `build/plugin/Release/obs-sei-stamper.dll`
   - Or use `out/obs-studio/` directory structure for easy installation


---

## Troubleshooting

### Issue: Encoder not appearing in OBS

**Solution:** 
- Verify plugin DLL is in `obs-plugins/64bit/` directory
- Check OBS logs for loading errors
- Ensure OBS version is 28.0+

### Issue: Receiver cannot connect to SRT

**Solution:**
- Verify `srt.dll` is installed
- Check firewall settings
- Confirm SRT URL format: `srt://ip:port`

### Issue: SEI data not found

**Solution:**
- Ensure NTP server is accessible
- Verify "Enable NTP Sync" is checked
- Check OBS logs for NTP sync status

---

## Performance

- **CPU Overhead**: < 1% (SEI insertion)
- **NTP Sync Frequency**: Every 60 seconds
- **Frame Accuracy**: ±1 frame at 60fps
- **Latency**: ~100ms (SRT with 120ms latency setting)

---

## License

GPL-2.0 License - following OBS Studio licensing

---

## Credits

- **OBS Studio**: https://obsproject.com
- **libsrt**: https://github.com/Haivision/srt
- **FFmpeg**: https://ffmpeg.org
- **NTP Protocol**: RFC 5905

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/obs-sei-stamper/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/obs-sei-stamper/wiki)

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Guidelines

1. Follow the existing code style
2. Add comments for complex logic
3. Test your changes thoroughly
4. Update documentation as needed

---

## License

GPL-2.0 License - following OBS Studio licensing

See [LICENSE](LICENSE) file for details.

---

## Credits

- **OBS Studio**: https://obsproject.com
- **libsrt**: https://github.com/Haivision/srt
- **FFmpeg**: https://ffmpeg.org
- **NTP Protocol**: RFC 5905

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/obs-sei-stamper/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/obs-sei-stamper/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/obs-sei-stamper/wiki)

---

## Release Notes

### v1.1.3 (2026-01-04)

**✨ New Features:**
- ⚙️ **Custom Receiver Sync Interval**: Added `NTP Sync Interval` setting to the receiver
  - Users can now customize the minimum time between NTP syncs
  - Range: 100ms to 1 hour (Default: 10s)
  - Replaces the hardcoded 10s backoff limit, giving full control to the user
  - **Warning**: Setting this too low (e.g., < 1000ms) may cause stuttering on slow networks
  - Added in-context UI warning to guide users

### v1.1.2 (2026-01-04)

**🔧 Bug Fixes:**
- 🐛 **Fixed Receiver Stuttering**: Critical performance fix for NTP synchronization
  - Added minimum 10-second interval for keyframe-triggered NTP sync
  - Prevents excessive network requests (was triggering every 2 seconds)
  - Resolves video playback stuttering issues
- 🛡️ **Network Resilience**: Added intelligent backoff mechanism
  - Prevents retry storms when NTP server is unreachable
  - Enforces wait intervals even after failed sync attempts
  - Ensures stream stability under poor network conditions
- 📝 **Updated Documentation**: Added NTP configuration recommendations

**Technical Details:**
- Receiver now enforces 10-second minimum between NTP syncs
- Keyframe sync: `is_keyframe && (time_since_last_sync >= 10s)`
- Drift detection remains unchanged (user-configurable threshold)
- Performance impact: Eliminated 5-500ms blocking calls every 2 seconds

**Migration**: No configuration changes required. Plugin will automatically use optimized sync strategy.

---

### v1.1.1 (2026-01-04)

**🔧 Improvements:**
- ✨ **Intelligent Receiver NTP Sync**: Implemented adaptive NTP synchronization strategy
  - Automatic sync on keyframes for high accuracy
  - Drift detection with 50ms threshold to prevent clock drift
  - Significantly improved long-running stability
- 📝 **Enhanced Documentation**: Added detailed NTP synchronization strategy documentation

**Technical Details:**
- Receiver now syncs NTP time on every keyframe
- Additional sync triggered when time drift exceeds 50ms
- Eliminated the "sync once on startup" limitation
- Better handling of long-running streams

---

### v1.1.0 (2026-01-04)

**🎉 New Features:**
- ✨ **NVIDIA NVENC Support**: Added hardware-accelerated H.264 encoding for NVIDIA GPUs
- ✨ **AMD AMF Support**: Added hardware-accelerated H.264 encoding for AMD GPUs
- 🚀 **Multi-GPU Support**: Users can now choose from Intel QuickSync, NVIDIA NVENC, or AMD AMF encoders

**Technical Details:**
- New encoder IDs: `h264_nvenc_native`, `h264_amf_native`
- Both new encoders support SEI timestamp insertion and NTP synchronization
- Uses FFmpeg backend for NVENC and AMD encoding
- All encoders share the same SEI UUID for compatibility

**Compatibility:**
- Requires compatible GPU hardware
- FFmpeg with NVENC/AMF support (included in release builds)
- Backward compatible with v1.0.0 streams

---

### v1.0.0 (2026-01-04)

**Initial Release:**
- Frame-level video synchronization using NTP timestamps
- Intel QuickSync H.264 encoder with SEI support
- SRT receiver with SEI extraction
- NTP client for time synchronization

---

**Current Version**: 1.1.3  
**Last Updated**: 2026-01-04

