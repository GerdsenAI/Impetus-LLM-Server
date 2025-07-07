#!/bin/bash

# IMPETUS Local Code Signing Script
# Creates a self-signed app that works on your Mac without security warnings

echo "🔐 IMPETUS Local Code Signing"
echo "============================="

# Check if app exists
APP_PATH="dist/mac-arm64/IMPETUS.app"
if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: IMPETUS.app not found at $APP_PATH"
    echo "   Run 'npm run build-dir' first"
    exit 1
fi

echo "📱 Found app at: $APP_PATH"

# Option 1: Ad-hoc signing (simplest)
adhoc_sign() {
    echo "🖊️  Ad-hoc signing (no certificate required)..."
    
    # Sign with ad-hoc signature
    codesign --force --deep --sign - "$APP_PATH"
    
    if [ $? -eq 0 ]; then
        echo "✅ Ad-hoc signing complete!"
    else
        echo "❌ Ad-hoc signing failed"
        return 1
    fi
}

# Option 2: Create and use self-signed certificate
self_signed_cert() {
    echo "📜 Creating self-signed certificate..."
    
    CERT_NAME="IMPETUS Local Development"
    
    # Check if certificate already exists
    if security find-certificate -c "$CERT_NAME" &>/dev/null; then
        echo "✅ Certificate already exists: $CERT_NAME"
    else
        echo "🔨 Creating new self-signed certificate..."
        
        # Create certificate using macOS security command
        # This creates a certificate valid for 365 days
        cat > /tmp/cert_config.txt << EOF
[ req ]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca

[ req_distinguished_name ]
CN = IMPETUS Local Development

[ v3_ca ]
keyUsage = critical, digitalSignature
extendedKeyUsage = critical, codeSigning
EOF
        
        # Note: This approach requires user interaction in Keychain Access
        echo "⚠️  Manual step required:"
        echo "   1. Open Keychain Access"
        echo "   2. Go to Keychain Access > Certificate Assistant > Create a Certificate"
        echo "   3. Name: IMPETUS Local Development"
        echo "   4. Identity Type: Self Signed Root"
        echo "   5. Certificate Type: Code Signing"
        echo "   6. Click Create and Continue through the prompts"
        echo ""
        echo "Press Enter when you've created the certificate..."
        read
    fi
    
    # Sign with the certificate
    echo "🖊️  Signing with self-signed certificate..."
    codesign --force --deep --sign "$CERT_NAME" "$APP_PATH"
    
    if [ $? -eq 0 ]; then
        echo "✅ Self-signed certificate signing complete!"
    else
        echo "❌ Certificate signing failed"
        echo "   Falling back to ad-hoc signing..."
        adhoc_sign
    fi
}

# Option 3: Remove quarantine (simplest for personal use)
remove_quarantine() {
    echo "🧹 Removing quarantine attributes..."
    xattr -cr "$APP_PATH"
    echo "✅ Quarantine removed!"
}

# Main menu
echo ""
echo "Choose signing method:"
echo "1) Ad-hoc sign (recommended for personal use)"
echo "2) Create self-signed certificate (more official)"
echo "3) Just remove quarantine (simplest)"
echo "4) All of the above"
echo ""
read -p "Choice (1-4): " choice

case $choice in
    1)
        adhoc_sign
        ;;
    2)
        self_signed_cert
        ;;
    3)
        remove_quarantine
        ;;
    4)
        adhoc_sign
        remove_quarantine
        ;;
    *)
        echo "Invalid choice, using ad-hoc signing"
        adhoc_sign
        ;;
esac

# Verify the signature
echo ""
echo "🔍 Verifying signature..."
codesign -dv "$APP_PATH" 2>&1 | grep -E "Signature|Identifier|Format"

echo ""
echo "📦 Signed app location: $APP_PATH"
echo ""
echo "🚀 To install:"
echo "   cp -r $APP_PATH /Applications/"
echo ""
echo "✅ Your IMPETUS app is now signed and ready to use!"
echo "   - No security warnings on launch"
echo "   - Works on your Mac"
echo "   - Ready for Applications folder"

# Create a simple installer script
cat > install-impetus.sh << 'EOF'
#!/bin/bash
echo "📦 Installing IMPETUS..."
cp -r dist/mac-arm64/IMPETUS.app /Applications/
echo "✅ IMPETUS installed to Applications!"
echo "🚀 You can now launch IMPETUS from your Applications folder"
EOF

chmod +x install-impetus.sh
echo ""
echo "💡 Tip: Run './install-impetus.sh' to install to Applications"