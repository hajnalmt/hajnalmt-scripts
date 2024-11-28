package main

import (
	"hajnalmt.hu/gin-example/db"
	"hajnalmt.hu/gin-example/routes"

	"github.com/gin-gonic/gin"
)

func main() {
	db.InitDB()
	server := gin.Default()
	routes.RegisterRoutes(server)
	server.Run(":8080")
}
