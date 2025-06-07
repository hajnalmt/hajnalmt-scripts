package ncoreproxy

import (
	"net/http"
)

// RegisterRoutes wires all route handlers to the default HTTP mux.
func RegisterRoutes(client *http.Client) {
	http.HandleFunc("/proxy-static/", func(w http.ResponseWriter, r *http.Request) {
		StaticProxy().ServeHTTP(w, r)
	})

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		MainProxy(client).ServeHTTP(w, r)
	})

	http.HandleFunc("/exit.php", HandleBlockedLogout)
	http.HandleFunc("/invites", HandleBlockedLogout)
}
