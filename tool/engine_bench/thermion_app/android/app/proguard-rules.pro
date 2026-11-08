# Thermion's JNI shim looks up dev.thermion.android.NativeWindowHelper$Companion
# by name (FindClass in ThermionFlutterAndroid.cpp). The default
# "keep native methods" rule should already cover it; this makes it explicit
# so R8 in release builds can never rename it.
-keep class dev.thermion.android.NativeWindowHelper { *; }
-keep class dev.thermion.android.NativeWindowHelper$Companion { *; }
