package io

import (
	"fmt"
	"github.com/akshaybabloo/dotfile-updater/models"
	"github.com/akshaybabloo/dotfile-updater/pkg/utils"
	"iter"
	"os"
	"path/filepath"
)

// ReadYamlFiles reads all the yaml files in the provided path
func ReadYamlFiles(p string) (iter.Seq2[models.Binaries, error], error) {
	abs, err := filepath.Abs(filepath.Join(p, "*.yaml"))
	if err != nil {
		return nil, fmt.Errorf("failed to get absolute path: %w", err)
	}

	glob, err := filepath.Glob(abs)
	if err != nil {
		return nil, fmt.Errorf("failed to glob files: %w", err)
	}

	return func(yield func(models.Binaries, error) bool) {
		for _, s := range glob {
			file, err := os.ReadFile(s)
			if err != nil {
				if !yield(models.Binaries{}, fmt.Errorf("error reading file %s: %w", s, err)) {
					return
				}
				continue
			}

			config, err := utils.ParseYaml(file)
			if err != nil {
				if !yield(models.Binaries{}, fmt.Errorf("error parsing YAML from file %s: %w", s, err)) {
					return
				}
				continue
			}

			if !yield(config, nil) {
				return
			}
		}
	}, nil
}
