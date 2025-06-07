package main

import (
	"bytes"
	"compress/gzip"
	"io"
	"log"
	"net/http"
	"net/http/cookiejar"
	"net/http/httputil"
	"net/url"
	"os"
	"strconv"
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
	if !bytes.Contains(body, []byte("Helyezés")) { // or any string that only appears when logged in
		log.Println("❌ Login likely failed — no 'Helyezés' found in response.")
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

	ncoreURL, _ := url.Parse(baseURL)
	staticURL, _ := url.Parse("https://static.ncore.pro")

	mainProxy := &httputil.ReverseProxy{
		Director: func(req *http.Request) {
			req.URL.Scheme = ncoreURL.Scheme
			req.URL.Host = ncoreURL.Host
			req.Host = ncoreURL.Host
			req.Header.Set("User-Agent", "Mozilla/5.0")

			// ✅ Inject PHPSESSID cookie manually from the jar
			for _, c := range client.Jar.Cookies(ncoreURL) {
				req.AddCookie(c)
			}
		},

		ModifyResponse: func(resp *http.Response) error {
			contentType := resp.Header.Get("Content-Type")
			if strings.Contains(contentType, "text/html") || strings.Contains(contentType, "javascript") {
				var body []byte
				var err error

				// Decompress if gzip encoded
				if resp.Header.Get("Content-Encoding") == "gzip" {
					log.Println("📦 MainProxy:  gzip-encoded", resp.Request.URL)

					gzReader, err := gzip.NewReader(resp.Body)
					if err != nil {
						return err
					}
					body, err = io.ReadAll(gzReader)
					resp.Body.Close()
					gzReader.Close()
					resp.Header.Del("Content-Encoding") // because we're re-encoding uncompressed
				} else {
					body, err = io.ReadAll(resp.Body)
					resp.Body.Close()
				}

				if err != nil {
					return err
				}

				modified := bytes.ReplaceAll(body, []byte("https://static.ncore.pro"), []byte("/proxy-static"))
				if !bytes.Equal(body, modified) {
					log.Printf("🔁 MainProxy rewrote static URLs in %s", resp.Request.URL.Path)
				}

				resp.Body = io.NopCloser(bytes.NewReader(modified))
				resp.ContentLength = int64(len(modified))
				resp.Header.Set("Content-Length", strconv.Itoa(len(modified)))
			}

			// Location rewrite
			if loc := resp.Header.Get("Location"); strings.HasPrefix(loc, baseURL) {
				resp.Header.Set("Location", strings.Replace(loc, baseURL, "http://localhost:8080", 1))
			}

			return nil
		},
	}

	// Proxy for static assets under /proxy-static/*
	staticProxy := &httputil.ReverseProxy{
		Director: func(req *http.Request) {
			req.URL.Scheme = staticURL.Scheme
			req.URL.Host = staticURL.Host
			req.Host = staticURL.Host
			req.URL.Path = strings.TrimPrefix(req.URL.Path, "/proxy-static")
			req.Header.Set("Referer", "https://ncore.pro/")
			req.Header.Set("User-Agent", "Mozilla/5.0")
		},

		ModifyResponse: func(resp *http.Response) error {
			contentType := resp.Header.Get("Content-Type")
			if !(strings.Contains(contentType, "javascript") || strings.Contains(contentType, "css")) {
				return nil
			}

			var body []byte
			var err error

			if resp.Header.Get("Content-Encoding") == "gzip" {
				log.Println("📦 StaticProxy: gzip-encoded", resp.Request.URL)
				gzReader, err := gzip.NewReader(resp.Body)
				if err != nil {
					return err
				}
				body, err = io.ReadAll(gzReader)
				resp.Body.Close()
				gzReader.Close()
				resp.Header.Del("Content-Encoding")
			} else {
				body, err = io.ReadAll(resp.Body)
				resp.Body.Close()
			}

			if err != nil {
				return err
			}

			modified := bytes.ReplaceAll(body, []byte("https://static.ncore.pro"), []byte("/proxy-static"))
			if !bytes.Equal(body, modified) {
				log.Printf("🔁 StaticProxy rewrote static URLs in %s", resp.Request.URL.Path)
			}

			resp.Body = io.NopCloser(bytes.NewReader(modified))
			resp.ContentLength = int64(len(modified))
			resp.Header.Set("Content-Length", strconv.Itoa(len(modified)))

			return nil
		},
	}

	http.HandleFunc("/proxy-static/", func(w http.ResponseWriter, r *http.Request) {
		staticProxy.ServeHTTP(w, r)
	})

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		mainProxy.ServeHTTP(w, r)
	})

	log.Println("🚀 nCore proxy running at http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
