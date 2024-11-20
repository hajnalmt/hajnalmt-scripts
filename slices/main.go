package main

import "fmt"

type Product struct {
	title string
	id    int
	price float64
}

func main() {
	var hobbies = [3]string{"Reading", "Coding", "Gaming"}
	fmt.Println(hobbies)
	fmt.Println(hobbies[0])
	fmt.Println(hobbies[1:])

	var slices1 = hobbies[0:2]
	var slices2 = hobbies[1:3]

	slices1 = hobbies[1:3]

	fmt.Println(slices1)
	fmt.Println(slices2)
	var goals = []string{"Learn Go", "Create a project"}
	goals[1] = "Create a website for the project"
	goals = append(goals, "Deploy the website")
	fmt.Println(goals)

	var products = []Product{{title: "Book", id: 1, price: 10.99}, {title: "Laptop", id: 2, price: 999.99}}
	products = append(products, Product{title: "Book", id: 2, price: 10.99})
	fmt.Println(products)
}

// Time to practice what you learned!

// 1) Create a new array (!) that contains three hobbies you have
// 		Output (print) that array in the command line.
// 2) Also output more data about that array:
//		- The first element (standalone)
//		- The second and third element combined as a new list
// 3) Create a slice based on the first element that contains
//		the first and second elements.
//		Create that slice in two different ways (i.e. create two slices in the end)
// 4) Re-slice the slice from (3) and change it to contain the second
//		and last element of the original array.
// 5) Create a "dynamic array" that contains your course goals (at least 2 goals)
// 6) Set the second goal to a different one AND then add a third goal to that existing dynamic array
// 7) Bonus: Create a "Product" struct with title, id, price and create a
//		dynamic list of products (at least 2 products).
//		Then add a third product to the existing list of products.
