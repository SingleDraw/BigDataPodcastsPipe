#!/bin/sh
# ==========================================================
# S3 Volume Mounting Configuration
# ==========================================================
mount_s3_volume() {

    #
    # Config.json
    # 
    cat <<EOF > /etc/seaweedfs/config.json
{
    "identities": [
      {
        "name": "anonymous",
        "actions": [
          "Read"
        ]
      },
      {
        "name": "data_stack_admin",
        "credentials": [
          {
            "accessKey": "$(cat "$S3_ACCESS_KEY_FILE")",
            "secretKey": "$(cat "$S3_SECRET_KEY_FILE")"
          }
        ],
        "actions": [
          "Admin",
          "Read",
          "List",
          "Tagging",
          "Write"
        ]
      }
    ]
  }
EOF

    #
    # Filer.toml
    #
    cat <<EOF > /etc/seaweedfs/filer.toml
[leveldb2]
enabled = true
dir = "/data/filerldb2"

[s3]
allow_anonymous = false
secret_key = "$(cat "$S3_SECRET_KEY_FILE")"
access_key = "$(cat "$S3_ACCESS_KEY_FILE")"
EOF

}


# ==========================================================
# S3 Keys Configuration
# ==========================================================
set_s3_keys() {
    S3_ACCESS_KEY=$(cat "${S3_ACCESS_KEY_FILE:-/run/secrets/s3_access_key}")
    export S3_ACCESS_KEY
    S3_SECRET_KEY=$(cat "${S3_SECRET_KEY_FILE:-/run/secrets/s3_secret_key}")
    export S3_SECRET_KEY
}

# ==========================================================
# Role-based Configuration
# ==========================================================
case "$1" in
  s3)
    set_s3_keys
    mount_s3_volume
    ;;
  master)
    set_s3_keys
    ;;
  *)
    echo "Unknown role: $1"
    exit 1
    ;;
esac

exec /entrypoint.sh "$@"
