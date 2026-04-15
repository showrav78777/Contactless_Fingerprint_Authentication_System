#!/bin/bash

echo "Updating iOS dependencies and rebuilding project..."

# Clean Flutter
echo "Cleaning Flutter..."
flutter clean

# Get Flutter dependencies
echo "Getting Flutter dependencies..."
flutter pub get

# Clean iOS build
echo "Cleaning iOS build..."
cd ios
rm -rf Pods
rm -rf Podfile.lock
rm -rf .symlinks
rm -rf Flutter/Flutter.framework
rm -rf Flutter/Flutter.podspec

# Install pods
echo "Installing CocoaPods dependencies..."
pod install --repo-update

# Go back to root
cd ..

# Build for iOS
echo "Building for iOS..."
flutter build ios --no-codesign

echo "iOS update complete!"
echo "You can now open ios/Runner.xcworkspace in Xcode and run the app." 