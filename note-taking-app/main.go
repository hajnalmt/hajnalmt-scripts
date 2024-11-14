package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"hajnalmt.hu/note/note"
	"hajnalmt.hu/note/todo"
)

type saver interface {
	Save() error
}

type outputtable interface {
	saver
	Display()
}

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

	err = outputData(todo)

	if err != nil {
		fmt.Println("Error saving todo:", err)
	}

	fmt.Println("Todo saved successfully!")

	err = outputData(userNote)
	if err != nil {
		fmt.Println(err)
	}
}

func saveData(data saver) error {
	err := data.Save()
	if err != nil {
		fmt.Println("Saving the note failed data:")
		return err
	}

	fmt.Println("Data saved successfully!")
	return nil
}

func outputData(data outputtable) error {
	data.Display()
	return saveData(data)
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
