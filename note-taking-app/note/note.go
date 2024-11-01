package note

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strings"
	"time"
)

type Note struct {
	title     string
	content   string
	createdAt time.Time
}

func New(title, content string) (Note, error) {
	if title == "" || content == "" {
		return Note{}, errors.New("title and content cannot be empty")
	}
	return Note{title: title, content: content, createdAt: time.Now()}, nil
}

func (note Note) Save() error {
	filename := strings.ReplaceAll(note.title, " ", "_")
	filename = strings.ToLower(filename)
	json, err := json.Marshal(note)
	if err != nil {
		return err
	}

	return os.WriteFile(filename, json, 0644)
}

func (note Note) Display() {
	fmt.Printf("Your note titled %v has the following content:\n\n%v\n", note.title, note.content)
}
