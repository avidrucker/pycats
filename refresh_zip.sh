#!/bin/bash

# Step 1: Delete the existing pycats.zip file if it exists
if [ -f pycats.zip ]; then
    echo "Removing existing pycats.zip..."
    rm pycats.zip
fi

# Step 2: Find and delete all __pycache__ directories within pycats/
echo "Deleting all __pycache__ folders inside pycats/..."
find pycats/ -type d -name "__pycache__" -exec rm -r {} +

# Step 3: Create a fresh zip file of the pycats/ directory
echo "Creating new pycats.zip..."
zip -r pycats.zip pycats/

echo "Done!"

