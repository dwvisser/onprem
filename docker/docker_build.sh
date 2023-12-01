#!/usr/bin/env bash

function print_guide() {
    echo "Usage: $0"
    echo
    echo "NVIDIA CUDA support version will be automatically detected. Only"
    echo "versions 11 and 12 are supported."

}

# Only allow script to run as root
if [ "$EUID" -ne 0 ]
then
    echo "This script must be run with sudo."
    exit 1
fi

# Get the directory of the script, and change to it
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$script_dir"

function build_cpu_image() {
    echo "Building the CPU-only image, called onprem:cpu."
    docker build -t onprem:cpu -f Dockerfile-cpu ..
}

# Is the necessary NVIDIA stuff installed? Technically, we could build the image
# without, but it is assumed that the container image will be used locally.
if ! command -v nvidia-smi >/dev/null 2>&1
then
  echo "The nvidia-smi executable is not present. Are you sure you have an"
  echo "NVIDIA device with NVIDIA drivers installed? Don't worry! I'll still"
  echo "build you a CPU-only image."
  build_cpu_image
  exit
fi

# Are we building CUDA 12 or CUDA 11?
cuda_version=`nvidia-smi | grep -P -o "CUDA Version: \d+(\.\d+)*" | grep -P -o "\d+" | head -n 1`
echo "Detected driver supporting CUDA ${cuda_version}."
if [ "$cuda_version" -ne 11 ] && [ "$cuda_vesion" -ne 12 ]
then
    echo "This script can only build CUDA images for CUDA 11 or 12. Don't"
    echo "worry! I'll still build you a cpu-only image."
    build_cpu_image
    exit
fi

# Set the suffix of the Dockerfile to use
tag="12.3.0"
if [ "$cuda_version" -eq 11 ]; then
    tag="11.8.0"
fi
cuda_image=${tag}-devel-ubuntu22.04

echo "Building onprem_cuda:$tag based on nvidia/cuda:$cuda_image"
docker build --build-arg CUDA_IMAGE=$cuda_image -t onprem_cuda:$tag -f Dockerfile-cuda ..

build_cpu_image
