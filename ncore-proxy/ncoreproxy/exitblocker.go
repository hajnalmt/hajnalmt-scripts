package ncoreproxy

import (
	"fmt"
	"log"
	"net/http"
)

func HandleBlockedLogout(w http.ResponseWriter, r *http.Request) {
	log.Printf("🛑 Kilépési kísérlet blokkolva: %s\n", r.RemoteAddr)

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.WriteHeader(http.StatusOK)

	fmt.Fprint(w, `
<!DOCTYPE html>
<html lang="hu">
<head>
  <meta charset="UTF-8">
  <title>Szép próbálkozás 😎</title>
  <style>
    body {
      background: #fff9db;
      color: #333;
      font-family: 'Segoe UI', sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
      text-align: center;
    }
    .container {
      max-width: 600px;
    }
    h1 {
      color: #d6336c;
      font-size: 2em;
    }
    a {
      display: inline-block;
      margin-top: 1rem;
      color: #0b7285;
      text-decoration: none;
      font-weight: bold;
    }
    a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🚫 Nem mész te innen sehova!</h1>
    <p>Ez túl jó móka, hogy csak úgy kilépj.</p>
    <p><em>A munkameneted biztonságban van. Ülj le, nyugi van.</em></p>
    <a href="/">⏪ Vissza a főoldalra</a>
  </div>
</body>
</html>
`)
}
