#!/bin/bash
flatc=$(dirname $0)/../../../public/bin/oss.flatbuffers/ubuntu22-gcc-x64/release/flatc
rm -frv ./bfbs 
rm -frv ./comm/datalayer/daq 
mkdir -pv ./bfbs 

$flatc --schema --gen-object-api --gen-compare --no-warnings --csharp ./fbs/*
$flatc --schema --binary --bfbs-comments -o ./bfbs ./fbs/*
