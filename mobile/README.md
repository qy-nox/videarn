# ClipEarn Mobile

Flutter Material 3 mobile client foundation for Android and future iOS support.

## Run

Install Flutter 3.22+ and configure Firebase for the target Android project first. Then:

```bash
cd mobile
flutter pub get
flutter gen-l10n
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
```

For a physical device, replace `10.0.2.2` with the development machine's LAN address.
Firebase ID-token login must be wired to the Firebase project before production authentication.

## Test

```bash
flutter test
```

Phase 5 includes the connected feed, comments, likes, search, profile, wallet summary, Firebase
email/password authentication, and a real gallery-to-presigned-upload flow. Configure Firebase
for Android and the S3/R2 values for the backend before testing those integrations.
