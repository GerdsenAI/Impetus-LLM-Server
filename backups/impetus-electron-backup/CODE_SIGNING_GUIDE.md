# Code Signing Guide for IMPETUS

## 📝 Overview

Code signing your IMPETUS app provides several benefits:
- ✅ No security warnings on first launch
- ✅ Smooth installation experience  
- ✅ Can be distributed outside the App Store
- ✅ Gatekeeper approval
- ✅ Notarization support for enhanced security

## 🔐 Prerequisites

You'll need an Apple Developer account to code sign applications. There are two options:

### Option 1: Free Apple Developer Account
- **Cost**: Free
- **Limitations**: Certificate expires every 7 days, apps only run on your Mac
- **Good for**: Personal use and testing

### Option 2: Paid Apple Developer Program
- **Cost**: $99/year
- **Benefits**: 
  - Developer ID certificates (valid for years)
  - Apps can run on any Mac
  - Notarization support
  - App Store distribution (if desired)
- **Good for**: Distribution to others

## 🛠️ Setup Steps

### Step 1: Create Apple Developer Account

1. **Free Account**:
   - Sign in with your Apple ID at [developer.apple.com](https://developer.apple.com)
   - This is automatic with any Apple ID

2. **Paid Account**:
   - Go to [developer.apple.com/programs](https://developer.apple.com/programs)
   - Click "Enroll" and follow the steps
   - Pay the $99 annual fee

### Step 2: Install Xcode (if not already installed)

```bash
# Install Xcode from the App Store or:
xcode-select --install
```

### Step 3: Create Certificates

#### For Free Account (via Xcode):
1. Open Xcode
2. Go to Preferences > Accounts
3. Add your Apple ID
4. Click "Manage Certificates"
5. Click "+" and create a "Mac Development" certificate

#### For Paid Account:
1. Go to [developer.apple.com/account](https://developer.apple.com/account)
2. Navigate to Certificates, IDs & Profiles
3. Create a "Developer ID Application" certificate
4. Download and install the certificate

### Step 4: Verify Certificate Installation

```bash
# Check if certificates are installed
security find-identity -v -p codesigning

# You should see something like:
# 1) XXXXXXXXXX "Developer ID Application: Your Name (TEAMID)"
```

## 🚀 Building Code-Signed IMPETUS

### Step 1: Configure package.json

Add your team ID and identity to the build configuration:

```json
{
  "build": {
    "mac": {
      "identity": "Developer ID Application: Your Name (TEAMID)",
      "hardenedRuntime": true,
      "gatekeeperAssess": false,
      "entitlements": "resources/entitlements.mac.plist",
      "entitlementsInherit": "resources/entitlements.mac.plist"
    }
  }
}
```

### Step 2: Create Environment Variables

```bash
# Set your Apple ID for notarization (paid accounts only)
export APPLE_ID="your-apple-id@email.com"
export APPLE_ID_PASSWORD="your-app-specific-password"
export APPLE_TEAM_ID="YOURTEAMID"
```

### Step 3: Build Signed App

```bash
# For basic code signing
npm run build-mac

# For signing + notarization (paid accounts only)
CSC_IDENTITY_AUTO_DISCOVERY=true npm run build-mac
```

## 🎯 Quick Code Signing (Without Developer Account)

If you just want to remove the quarantine flag locally:

```bash
# Option 1: Remove quarantine attribute
xattr -cr /Applications/IMPETUS.app

# Option 2: Self-sign with ad-hoc certificate
codesign --force --deep --sign - /Applications/IMPETUS.app

# Option 3: Create a self-signed certificate
# 1. Open Keychain Access
# 2. Certificate Assistant > Create a Certificate
# 3. Name: "IMPETUS Development"
# 4. Identity Type: Self Signed Root
# 5. Certificate Type: Code Signing
# 6. Use the certificate to sign:
codesign --force --deep --sign "IMPETUS Development" /Applications/IMPETUS.app
```

## 📦 Automated Build Script

Create `build-signed.sh`:

```bash
#!/bin/bash

# Check for signing identity
IDENTITY=$(security find-identity -v -p codesigning | grep "Developer ID Application" | head -1 | awk '{print $2}')

if [ -z "$IDENTITY" ]; then
    echo "❌ No Developer ID certificate found"
    echo "Creating self-signed certificate instead..."
    
    # Create self-signed certificate
    security create-keychain -p "" build.keychain
    security default-keychain -s build.keychain
    security unlock-keychain -p "" build.keychain
    security set-keychain-settings -t 3600 -u build.keychain
    
    # Build without Apple signing
    npm run build-mac
    
    # Self-sign the app
    codesign --force --deep --sign - "dist/mac*/IMPETUS.app"
    echo "✅ App self-signed (will only run on this Mac)"
else
    echo "✅ Found signing identity: $IDENTITY"
    # Build with proper signing
    CSC_IDENTITY_AUTO_DISCOVERY=true npm run build-mac
fi
```

## 🔍 Verification

After signing, verify your app:

```bash
# Check code signature
codesign -dv --verbose=4 /Applications/IMPETUS.app

# Verify signature
codesign --verify --deep --strict --verbose=2 /Applications/IMPETUS.app

# Check notarization status (paid accounts)
spctl -a -t exec -vvv /Applications/IMPETUS.app
```

## 🚨 Common Issues

### "errSecInternalComponent" Error
- Unlock your keychain: `security unlock-keychain`
- Reset keychain permissions

### Certificate Not Found
- Ensure certificate is in the login keychain
- Check certificate trust settings

### Notarization Failed
- Ensure all entitlements are correct
- Check for hardened runtime compliance
- Verify app-specific password is correct

## 🎁 Free Alternative: DMG with Instructions

For distribution without signing:

```bash
# Create a DMG with instructions
create-dmg \
  --volname "IMPETUS Installer" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "IMPETUS.app" 200 190 \
  --hide-extension "IMPETUS.app" \
  --app-drop-link 400 190 \
  --text-size 12 \
  --background "installer-background.png" \
  "IMPETUS-Installer.dmg" \
  "dist/mac-arm64/"
```

## 📝 Summary

- **Personal Use**: Self-signing or removing quarantine is sufficient
- **Small Distribution**: Free Apple Developer account + manual instructions
- **Wide Distribution**: Paid Developer account + proper signing + notarization

The current IMPETUS.app will work perfectly fine with any of these approaches!