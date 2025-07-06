#!/bin/bash
# Generate self-signed SSL certificates for development/testing

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Generating SSL certificates for Impetus LLM Server${NC}"

# Check if openssl is installed
if ! command -v openssl &> /dev/null; then
    echo -e "${RED}Error: OpenSSL is not installed${NC}"
    exit 1
fi

# Create certificates directory
CERT_DIR="certs"
mkdir -p "$CERT_DIR"

# Certificate details
COUNTRY="US"
STATE="California"
LOCALITY="San Francisco"
ORGANIZATION="Impetus Development"
UNIT="Development"
COMMON_NAME="localhost"
EMAIL="dev@impetus.local"

# Generate private key
echo -e "${GREEN}Generating private key...${NC}"
openssl genrsa -out "$CERT_DIR/server.key" 2048

# Generate certificate signing request
echo -e "${GREEN}Creating certificate signing request...${NC}"
openssl req -new -key "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" \
    -subj "/C=$COUNTRY/ST=$STATE/L=$LOCALITY/O=$ORGANIZATION/OU=$UNIT/CN=$COMMON_NAME/emailAddress=$EMAIL"

# Create extensions file for SAN (Subject Alternative Names)
cat > "$CERT_DIR/v3.ext" <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
DNS.3 = impetus.local
DNS.4 = *.impetus.local
IP.1 = 127.0.0.1
IP.2 = ::1
IP.3 = 0.0.0.0
EOF

# Generate self-signed certificate
echo -e "${GREEN}Generating self-signed certificate...${NC}"
openssl x509 -req -in "$CERT_DIR/server.csr" -signkey "$CERT_DIR/server.key" \
    -out "$CERT_DIR/server.crt" -days 365 -sha256 -extfile "$CERT_DIR/v3.ext"

# Create combined PEM file
echo -e "${GREEN}Creating combined PEM file...${NC}"
cat "$CERT_DIR/server.crt" "$CERT_DIR/server.key" > "$CERT_DIR/server.pem"

# Set appropriate permissions
chmod 600 "$CERT_DIR/server.key"
chmod 644 "$CERT_DIR/server.crt"
chmod 600 "$CERT_DIR/server.pem"

# Generate DH parameters for additional security (optional, takes time)
echo -e "${YELLOW}Generating DH parameters (this may take a minute)...${NC}"
openssl dhparam -out "$CERT_DIR/dhparam.pem" 2048

# Display certificate info
echo -e "${GREEN}Certificate generation complete!${NC}"
echo ""
echo "Certificate files created in '$CERT_DIR/':"
echo "  - server.key  : Private key"
echo "  - server.crt  : Certificate"
echo "  - server.pem  : Combined certificate and key"
echo "  - dhparam.pem : DH parameters"
echo ""
echo -e "${YELLOW}Certificate details:${NC}"
openssl x509 -in "$CERT_DIR/server.crt" -noout -subject -dates

# Create .env example for SSL
echo ""
echo -e "${GREEN}Add these to your .env file:${NC}"
echo "SSL_CERT_PATH=$CERT_DIR/server.crt"
echo "SSL_KEY_PATH=$CERT_DIR/server.key"
echo "SSL_PEM_PATH=$CERT_DIR/server.pem"
echo "SSL_DHPARAM_PATH=$CERT_DIR/dhparam.pem"

# Clean up
rm -f "$CERT_DIR/server.csr" "$CERT_DIR/v3.ext"

echo ""
echo -e "${YELLOW}⚠️  Note: This is a self-signed certificate for development only.${NC}"
echo -e "${YELLOW}   Browsers will show security warnings. For production, use a proper CA.${NC}"