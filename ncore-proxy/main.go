package main

import (
	"bytes"
	"io"
	"log"
	"net/http"
	"net/http/cookiejar"
	"net/http/httputil"
	"net/url"
	"os"
	"strings"
)

var (
	client  *http.Client
	baseURL = "https://ncore.pro"
)

func loginToNCore(username, password string) error {
	loginURL := baseURL + "/login.php"

	data := url.Values{}
	data.Set("set_lang", "hu")
	data.Set("submitted", "1")
	data.Set("nev", username)
	data.Set("pass", password)

	req, err := http.NewRequest("POST", loginURL, bytes.NewBufferString(data.Encode()))
	if err != nil {
		return err
	}

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
	if !bytes.Contains(body, []byte("hunolulu")) { // or any string that only appears when logged in
		log.Println("❌ Login likely failed — no 'Kijelentkezés' found in response.")
	} else {
		log.Println("✅ Login successful (HTML contains logged-in marker)")
	}

	log.Println("✅ Login successful")
	return nil
}

func main() {
	username := os.Getenv("NCORE_USERNAME")
	password := os.Getenv("NCORE_PASSWORD")

	if username == "" || password == "" {
		log.Fatal("Missing NCORE_USERNAME or NCORE_PASSWORD env vars")
	}

	jar, _ := cookiejar.New(nil)
	client = &http.Client{Jar: jar}

	if err := loginToNCore(username, password); err != nil {
		log.Fatalf("Login failed: %v", err)
	}

	target, _ := url.Parse(baseURL)

	proxy := &httputil.ReverseProxy{
		Director: func(req *http.Request) {
			req.URL.Scheme = target.Scheme
			req.URL.Host = target.Host
			req.Host = target.Host
			req.Header.Set("User-Agent", "Mozilla/5.0")

			// ✅ Inject PHPSESSID cookie manually from the jar
			cookies := client.Jar.Cookies(target)
			for _, cookie := range cookies {
				if cookie.Name == "PHPSESSID" {
					req.AddCookie(cookie)
				}
			}
		},

		ModifyResponse: func(resp *http.Response) error {
			location := resp.Header.Get("Location")

			if location != "" {
				log.Printf("🔁 Redirected to: %s (status: %d)\n", location, resp.StatusCode)
				if strings.HasPrefix(location, baseURL) {
					// Absolute redirect like: https://ncore.pro/somepage
					resp.Header.Set("Location", strings.Replace(location, baseURL, "http://localhost:8080", 1))
				} else if strings.HasPrefix(location, "/") {
					// Relative redirect like: /login.php
					resp.Header.Set("Location", "http://localhost:8080"+location)
				}
			}

			return nil
		},
	}

	log.Println("🚀 nCore proxy running at http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", proxy))
}
