#!/bin/bash

# Check if the required arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <package_name> <output_location>"
    exit 1
fi

PACKAGE_NAME=$1
OUTPUT_LOCATION=$2

# Define the source site-packages path
SOURCE_SITE_PACKAGES="/home/alice/btc_forecast_aws/.venv/lib/python3.10/site-packages"

# Define the layer structure
LAYER_DIR="lambda_layer"
LAYER_SITE_PACKAGES="$LAYER_DIR/python/lib/python3.10/site-packages"

# Clean up any previous layer directory
if [ -d "$LAYER_DIR" ]; then
    echo "Cleaning up previous layer directory..."
    rm -rf "$LAYER_DIR"
fi

# Create the directory structure
echo "Creating directory structure..."
mkdir -p "$LAYER_SITE_PACKAGES"

# Find the source package directory
echo "Searching for the package: $PACKAGE_NAME in $SOURCE_SITE_PACKAGES..."
SOURCE_DIR=$(find "$SOURCE_SITE_PACKAGES" -maxdepth 1 -name "$PACKAGE_NAME*" -type d)

if [ -z "$SOURCE_DIR" ]; then
    echo "Error: Package $PACKAGE_NAME not found in $SOURCE_SITE_PACKAGES."
    exit 1
else
    echo "Found package directories:"
    echo "$SOURCE_DIR"
fi

# Copy the package(s) to the layer directory
echo "Copying package(s) to the layer directory... "$LAYER_SITE_PACKAGES/""
for DIR in $SOURCE_DIR; do
    echo "Copying $DIR..."
    cp -r "$DIR" "$LAYER_SITE_PACKAGES/"
done


# Create the ZIP file
ZIP_FILE="$OUTPUT_LOCATION/${PACKAGE_NAME}_layer.zip"
if [ ! -d "$OUTPUT_LOCATION" ]; then
    echo "Creating output directory: $OUTPUT_LOCATION..."
    mkdir -p "$OUTPUT_LOCATION"
fi


echo "Zipping the layer directory... output: $ZIP_FILE input: $LAYER_DIR"
cd "$LAYER_DIR" || exit 1

# Ensure the `python` directory exists and is not empty
if [ -d "python" ] && [ "$(ls -A python)" ]; then
    zip -r "../$ZIP_FILE" python > /dev/null
    echo "ZIP file created successfully at $ZIP_FILE."
else
    echo "Error: No files to zip in the layer directory."
    exit 1
fi

cd - || exit 1

Clean up the layer directory
echo "Cleaning up temporary layer directory..."
rm -rf "$LAYER_DIR"

echo "Lambda layer for $PACKAGE_NAME created at: $ZIP_FILE"
