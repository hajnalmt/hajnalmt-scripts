package main

import (
	"errors"
	"fmt"

	"hajnalmt.hu/note/note"
)

type Note struct {
}

func main() {
	title, content := getNoteData()

	userNote, err := note.New(title, content)
	if err != nil {
		fmt.Println(err)
		return
	}

}

func getNodeData() (string, string) {
	title := getUserInput("Note title:")
	content := getUserInput("Note content:")
	return title, content
}

func getUserInput(prompt string) (string, error) {
	var input string
	fmt.Print(prompt)
	fmt.Scanln(&input)
	if input == "" {
		fmt.Println("Invalid input")
		return "", errors.New("invalid input")
	}
	return input, nil
}
