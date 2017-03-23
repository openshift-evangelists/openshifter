package main

import (
	"io"
	"os"
)

func copy(from, to string) error {
	src, err := os.Open(from)
	if err != nil {
		return err
	}
	defer src.Close()
	dest, err := os.Create(to)
	if err != nil {
		return err
	}
	defer dest.Close()
	_, err = io.Copy(dest, src)
	if err != nil {
		return err
	}
	err = dest.Sync()
	if err != nil {
		return err
	}
	return nil
}
