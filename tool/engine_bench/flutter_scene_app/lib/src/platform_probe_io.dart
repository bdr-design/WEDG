import 'dart:io';

import 'package:flutter_gpu/gpu.dart' as gpu;

/// Resident set size of this process, in bytes.
int? currentRssBytes() => ProcessInfo.currentRss;

/// Which Impeller backend Flutter GPU is running on.
///
/// Flutter GPU has no backend getter. Rendering into a non-zero mip level is
/// supported on Metal and Vulkan and not (yet) on Impeller's OpenGL ES
/// backend, so on Android it tells the two apart. Impeller also logs its
/// choice ("Using the Impeller rendering backend (...)") to logcat.
String gpuBackend() {
  try {
    if (Platform.isIOS || Platform.isMacOS) return 'metal';
    return gpu.gpuContext.doesSupportFramebufferRenderMipmap ? 'vulkan' : 'gles';
  } on Object {
    return 'unknown';
  }
}
