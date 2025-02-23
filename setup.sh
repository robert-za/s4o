#!/bin/sh
ln -s -f ../../git-hooks/pre-commit .git/hooks/pre-commit
ln -s -f ../../git-hooks/pre-push .git/hooks/pre-push
make build
