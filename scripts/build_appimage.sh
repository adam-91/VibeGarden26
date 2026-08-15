#!/bin/bash
set -euo pipefail

APP_NAME="VibeGarden26"
VERSION="0.1.0"
BUILD_DIR="dist/appimage"
APP_DIR="$BUILD_DIR/$APP_NAME.AppDir"

echo "Building $APP_NAME AppImage..."

pip install pyinstaller
pyinstaller --onefile --windowed \
    --name="$APP_NAME" \
    --add-data="resources:resources" \
    src/main.py

mkdir -p "$APP_DIR/usr/bin"
cp "dist/$APP_NAME" "$APP_DIR/usr/bin/"

cat > "$APP_DIR/$APP_NAME.desktop" <<EOF
[Desktop Entry]
Name=$APP_NAME
Exec=$APP_NAME
Icon=$APP_NAME
Type=Application
Categories=Office;Calendar;
EOF

cp resources/icons/app.png "$APP_DIR/$APP_NAME.png"

wget -q -O "$BUILD_DIR/appimagetool" \
    "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
chmod +x "$BUILD_DIR/appimagetool"

ARCH=x86_64 "$BUILD_DIR/appimagetool" "$APP_DIR" "dist/${APP_NAME}-${VERSION}.AppImage"

echo "AppImage created: dist/${APP_NAME}-${VERSION}.AppImage"
