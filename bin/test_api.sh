#!/bin/sh

#curl --json '{"F":"w","N":"test.json","D":{"A":123}}' http://localhost:40788/home/file
curl --json '{"F":"r","N":"test.json"}' http://localhost:40788/home/file
