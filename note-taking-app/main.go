package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"hajnalmt.hu/note/note"
	"hajnalmt.hu/note/todo"
)

func main() {
	title, content := getNoteData()
	todoContent := getUserInput("Todo content:")

	todo, err := todo.New(todoContent)
	if err != nil {
		fmt.Println(err)
		return
	}

	userNote, err := note.New(title, content)
	if err != nil {
		fmt.Println(err)
		return
	}

	todo.Display()
	err = todo.Save()

	if err != nil {
		fmt.Println("Error saving todo:", err)
	}

	fmt.Println("Todo saved successfully!")

	userNote.Display()

	err = userNote.Save()
	if err != nil {
		fmt.Println("Error saving note:", err)
	}

	fmt.Println("Note saved successfully!")
}

func getNoteData() (string, string) {
	title := getUserInput("Note title:")
	content := getUserInput("Note content:")
	return title, content
}

func getUserInput(prompt string) string {
	fmt.Printf("%v ", prompt)
	reader := bufio.NewReader(os.Stdin)
	text, err := reader.ReadString('\n')
	if err != nil {
		return ""
	}

	text = strings.TrimSuffix(text, "\n")
	text = strings.TrimSuffix(text, "\r")
	return text
}
