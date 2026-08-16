"""Test suite validating Task 2.1 Kotlin Multiplatform (KMP) Client repository structure."""

import os


def test_kmp_client_repository_structure():
    base_dir = "/Users/souvikojha/doctask-souvik-ojha/superdocs-kmp-client"

    assert os.path.exists(os.path.join(base_dir, "build.gradle.kts"))
    assert os.path.exists(os.path.join(base_dir, "settings.gradle.kts"))
    assert os.path.exists(os.path.join(base_dir, "README.md"))

    # CommonMain
    assert os.path.exists(os.path.join(base_dir, "src/commonMain/kotlin/app/superdocs/client/SuperDocsClient.kt"))
    assert os.path.exists(os.path.join(base_dir, "src/commonMain/kotlin/app/superdocs/client/models/Models.kt"))

    # AndroidMain
    assert os.path.exists(os.path.join(base_dir, "src/androidMain/kotlin/app/superdocs/client/work/DocumentWorker.kt"))
    assert os.path.exists(os.path.join(base_dir, "src/androidMain/kotlin/app/superdocs/client/provider/DocumentProviderAccess.kt"))

    # CommonTest
    assert os.path.exists(os.path.join(base_dir, "src/commonTest/kotlin/app/superdocs/client/SuperDocsClientTest.kt"))
