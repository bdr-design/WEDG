plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.marah.bench.thermion"
    compileSdk = flutter.compileSdkVersion
    // Thermion's Android plugin (thermion_flutter) builds its JNI shim with
    // NDK 28.2.13676358, the same as Flutter 3.47's default; keep them equal
    // so Gradle does not need a second NDK. The Filament/Thermion native
    // library itself is compiled by thermion_dart's Dart build hook with the
    // NDK that the Flutter tool finds (ANDROID_NDK_HOME, else the newest one
    // in the SDK).
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        applicationId = "com.marah.bench.thermion"
        // Thermion needs API 22+; Flutter's default (24) is above that.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    buildTypes {
        release {
            // Benchmark build: signed with the debug key so it installs.
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
