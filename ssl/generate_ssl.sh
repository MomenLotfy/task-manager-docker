
CERT_DIR="$(dirname "$0")/certs"
KEY_DIR="$(dirname "$0")/private"

echo "Creating SSL directories..."
mkdir -p "$CERT_DIR" "$KEY_DIR"

echo " Generating self-signed SSL certificate..."

openssl req -x509 \
  -nodes \
  -days 365 \
  -newkey rsa:2048 \
  -keyout "$KEY_DIR/nginx.key" \
  -out    "$CERT_DIR/nginx.crt" \
  -subj "/C=EG/ST=Cairo/L=Cairo/O=TaskManager/OU=DevOps/CN=localhost"

chmod 600 "$KEY_DIR/nginx.key"
chmod 644 "$CERT_DIR/nginx.crt"

echo ""
echo " SSL Certificate generated successfully!"
echo "   Certificate : $CERT_DIR/nginx.crt"
echo "   Private Key : $KEY_DIR/nginx.key"
echo ""
echo "Now run: docker compose up -d --build"
