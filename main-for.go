package main

import (
    "fmt"
    "log"
    "net/http"
    "net/http/cookiejar"
    "net/http/httputil"
    "net/url"
    "os"
    "strings"
    "sync"
)

var (
    client      *http.Client
    baseURL     = "https://ncore.pro"
    cookieMutex sync.RWMutex
)

func loginToNCore(username, password string) error {
    loginURL := baseURL + "/login.php"

    data := url.Values{}
    data.Set("nev", username)
    data.Set("pass", password)
    data.Set("login", "Belépés")

    req, err := http.NewRequest("POST", loginURL, strings.NewReader(data.Encode()))
    if err != nil {
        return err
    }

    req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
    req.Header.Set("User-Agent", "Mozilla/5.0") // helps avoid bot blocking

    resp, err := client.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusFound && resp.StatusCode != http.StatusOK {
        return fmt.Errorf("unexpected status: %s", resp.Status)
    }

    log.Println("✅ Login successful")
    return nil
}

func proxyHandler(w http.ResponseWriter, r *http.Request) {
    targetURL, _ := url.Parse(baseURL)

    proxy := httputil.NewSingleHostReverseProxy(targetURL)

    proxy.Director = func(req *http.Request) {
        req.URL.Scheme = "https"
        req.URL.Host = targetURL.Host
        req.URL.Path = r.URL.Path
        req.URL.RawQuery = r.URL.RawQuery
        req.Host = targetURL.Host

        req.Header.Set("User-Agent", "Mozilla/5.0")
        cookieMutex.RLock()
        for _, c := range client.Jar.Cookies(targetURL) {
            req.AddCookie(c)
        }
        cookieMutex.RUnlock()
    }

    proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
        http.Error(w, "Proxy error: "+err.Error(), http.StatusBadGateway)
    }

    proxy.ServeHTTP(w, r)
}

func main() {
    username := os.Getenv("NCORE_USERNAME")
    password := os.Getenv("NCORE_PASSWORD")

    if username == "" || password == "" {
        log.Fatal("Missing NCORE_USERNAME or NCORE_PASSWORD")
    }

    jar, err := cookiejar.New(nil)
    if err != nil {
        log.Fatalf("Failed to create cookie jar: %v", err)
    }

    client = &http.Client{
        Jar: jar,
    }

    if err := loginToNCore(username, password); err != nil {
        log.Fatalf("❌ Login failed: %v", err)
    }

    http.HandleFunc("/", proxyHandler)

    log.Println("🚀 nCore proxy running at http://localhost:8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
