package ncoreproxy

import (
	"bytes"
	"io"
	"log"
	"math/rand"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"os"
	"time"
)

const baseURL = "https://ncore.pro"

func InitClient() *http.Client {
	jar, _ := cookiejar.New(nil)
	return &http.Client{Jar: jar}
}

func Login(client *http.Client) error {
	username := os.Getenv("NCORE_USERNAME")
	password := os.Getenv("NCORE_PASSWORD")

	if username == "" || password == "" {
		log.Fatal("Missing NCORE_USERNAME or NCORE_PASSWORD env vars")
	}

	data := url.Values{}
	data.Set("set_lang", "hu")
	data.Set("submitted", "1")
	data.Set("nev", username)
	data.Set("pass", password)

	req, _ := http.NewRequest("POST", baseURL+"/login.php", bytes.NewBufferString(data.Encode()))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Set("User-Agent", "Mozilla/5.0")
	req.Header.Set("Origin", baseURL)
	req.Header.Set("Referer", baseURL+"/login.php")

	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	if !bytes.Contains(body, []byte("Helyezés")) {
		log.Println("❌ Login likely failed — no 'Helyezés' found.")
	} else {
		log.Println("✅ Login successful")
	}
	return nil
}

func ScheduleRelogin(client *http.Client) {
	go func() {
		for {
			// Relogin between 2 days and 3 weeks
			delay := time.Duration(rand.Intn(19*24)+48) * time.Hour
			log.Printf("⏰ Next relogin in %v", delay)
			time.Sleep(delay)
			if err := Login(client); err != nil {
				log.Printf("🔄 Relogin failed: %v", err)
			} else {
				log.Println("🔐 Relogin successful")
			}
		}
	}()
}
