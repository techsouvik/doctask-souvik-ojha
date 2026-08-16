plugins {
    kotlin("multiplatform") version "1.9.22"
    kotlin("plugin.serialization") version "1.9.22"
    id("com.android.library") version "8.2.2"
}

kotlin {
    jvm {
        compilation: org.jetbrains.kotlin.gradle.targets.jvm.KotlinJvmCompilation
    }
    androidTarget {
        publishLibraryVariants("release", "debug")
    }

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.8.0")
                implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.2")
                implementation("io.ktor:ktor-client-core:2.3.8")
                implementation("io.ktor:ktor-client-content-negotiation:2.3.8")
                implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.8")
                implementation("io.ktor:ktor-client-logging:2.3.8")
            }
        }
        val commonTest by getting {
            dependencies {
                implementation(kotlin("test"))
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.8.0")
            }
        }
        val jvmMain by getting {
            dependencies {
                implementation("io.ktor:ktor-client-cio:2.3.8")
            }
        }
        val androidMain by getting {
            dependencies {
                implementation("io.ktor:ktor-client-okhttp:2.3.8")
                implementation("androidx.work:work-runtime-ktx:2.9.0")
                implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
            }
        }
    }
}

android {
    namespace = "app.superdocs.client"
    compileSdk = 34
    defaultConfig {
        minSdk = 24
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
