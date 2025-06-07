package main

import (
	"log"
	"net/http"

	"github.com/hajnalmt/hajnalmt-scripts/ncore-proxy/ncoreproxy"
)

func main() {
	client := ncoreproxy.InitClient()

	if err := ncoreproxy.Login(client); err != nil {
		log.Fatalf("Login failed: %v", err)
	}

	go ncoreproxy.ScheduleRelogin(client)

	ncoreproxy.RegisterRoutes(client)

	log.Println("🚀 nCore proxy running at http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
