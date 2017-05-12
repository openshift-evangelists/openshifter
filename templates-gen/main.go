// This program generates a file templates/templates.go and
// populates it with the content of the templates in templates/ as strings.
// First, it reads template files (.tmpl or .tf) in the templates/ directory
// (and all directories below it) and then represents them as a map in templates.go:
// the relative file path of the template is the key and the content of the
// template file is the value as a string literal.
//
// Use templates.Asset() to retrieve the content of a template file.
// For example, the following loads the content of the template file
// templates/ansible.tmpl into data:
//
// data, err := templates.Asset("templates/ansible.tmpl")
package main

import (
	"bytes"
	"fmt"
	"go/format"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"
)

const (
	templatesDir = "templates/"

	header = `// Package templates makes the content of the template files
// (.tmpl|.tf) under the templates/ directory available as strings.
// Use templates.Asset() to get the content of a template.
//
// NOTE: THIS IS A GENERATED FILE - DON'T EDIT
//
package templates
import (
	"fmt"
	"path/filepath"
	"strings"
)

const (
`
	funcAsset = `
// Asset retrieves the content of the template file at filename as a string.
// Example: content, err := templates.Asset("templates/ansible.tmpl")
func Asset(filename string) (string, error) {
	if filename == "" {
		return "", fmt.Errorf("%s", "Can't look up empty template file")
	}
	base, _ := filepath.Abs(filepath.Dir("."))
	filename = strings.TrimPrefix(filename, "templates/")
	if val, ok := templates[keyit(base,filename)]; ok {
		return val, nil
	}
	return "", fmt.Errorf("Can't find template file %s", filename)
}
`
	mapTemplates = `
var templates = map[string]string{
`
	funcKeyit = `
func keyit(base, f string) string {
	if !strings.HasSuffix(base, "/") {
		base += "/"
	}
	k := strings.TrimPrefix(f, base)
	k = strings.Replace(k, "/", "", -1)
	k = strings.Replace(k, "-", "", -1)
	k = strings.Replace(k, ".", "", -1)
	return k
}
`
)

func main() {
	err := generate()
	if err != nil {
		fmt.Println(err)
		os.Exit(-1)
	}
}

func generate() error {
	dir, _ := filepath.Abs(filepath.Dir(templatesDir))
	b := bytes.NewBufferString("")
	templates, err := filter(dir)
	if err != nil {
		return fmt.Errorf("Can't read from %s: %s", dir, err)
	}
	bwrite(b, header)
	for _, f := range templates {
		bwrite(b, keyit(dir, f)+" = `")
		t, rerr := ioutil.ReadFile(f)
		if rerr != nil {
			return fmt.Errorf("Can't read template %s:%s", f, err)
		}
		bwrite(b, string(t))
		bwrite(b, "`\n")
	}
	bwrite(b, ")\n")
	bwrite(b, mapTemplates)
	for _, f := range templates {
		k := keyit(dir, f)
		bwrite(b, "\""+k+"\" : "+k+",\n")
	}
	bwrite(b, "}\n")
	bwrite(b, funcAsset)
	bwrite(b, funcKeyit)

	gofmtedb, err := format.Source(b.Bytes())
	if err != nil {
		return fmt.Errorf("Can't gofmt templates.go:%s", err)
	}
	err = twrite(bytes.NewBuffer(gofmtedb), dir)
	if err != nil {
		return err
	}
	return nil
}

func twrite(b *bytes.Buffer, dir string) error {
	out, err := os.Create(filepath.Join(dir, "templates.go"))
	if err != nil {
		return fmt.Errorf("Can't create templates.go: %s", err)
	}
	defer func() {
		_ = out.Close()
	}()
	_, err = out.Write(b.Bytes())
	if err != nil {
		return fmt.Errorf("Can't write to template: %s", err)
	}
	err = out.Sync()
	if err != nil {
		return fmt.Errorf("Can'tflush contents of templates.go to disk:%s", err)
	}
	return nil
}

func bwrite(b *bytes.Buffer, s string) {
	b.WriteString(s)
}

func filter(d string) ([]string, error) {
	templates := []string{}
	err := filepath.Walk(d, func(path string, f os.FileInfo, err error) error {
		if strings.HasSuffix(f.Name(), ".tmpl") || strings.HasSuffix(f.Name(), ".tf") {
			templates = append(templates, path)
			fmt.Println(path)
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	return templates, nil
}

// turns: /tmp/something/openshifter/templates/ansible.tmpl
// into: ansibletmpl
func keyit(base, f string) string {
	if !strings.HasSuffix(base, "/") {
		base += "/"
	}
	k := strings.TrimPrefix(f, base)
	k = strings.Replace(k, "/", "", -1)
	k = strings.Replace(k, "-", "", -1)
	k = strings.Replace(k, ".", "", -1)
	return k
}
