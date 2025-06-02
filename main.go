package main

import (
    "fmt"
    "io"
    "log"
    "net/http"
    "net/http/httputil"
    "net/url"
    "os"
    "strings"
    "sync"
)

var (
    client      = &http.Client{}
    cookieJar   []*http.Cookie
    cookieMutex sync.RWMutex
)

func loginToNCore(username, password string) error {
    loginURL := "https://ncore.pro/login.php"
    data := url.Values{}
    data.Set("nev", username)
    data.Set("pass", password)
    data.Set("login", "Belépés")

    req, err := http.NewRequest("POST", loginURL, strings.NewReader(data.Encode()))
    if err != nil {
        return err
    }

    req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

    resp, err := client.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusFound && resp.StatusCode != http.StatusOK {
        body, _ := io.ReadAll(resp.Body)
        return fmt.Errorf("login failed: %s", body)
    }

    // Save cookies
    cookieMutex.Lock()
    cookieJar = resp.Cookies()
    cookieMutex.Unlock()

    log.Println("Login successful")
    return nil
}

func proxyHandler(w http.ResponseWriter, r *http.Request) {
    targetURL := "https://ncore.pro"

    u, _ := url.Parse(targetURL)
    proxy := httputil.NewSingleHostReverseProxy(u)

    originalDirector := proxy.Director
    proxy.Director = func(req *http.Request) {
        originalDirector(req)

        // Set path/query
        req.URL.Path = r.URL.Path
        req.URL.RawQuery = r.URL.RawQuery

        // Inject login cookies
        cookieMutex.RLock()
        for _, c := range cookieJar {
            req.AddCookie(c)
        }
        cookieMutex.RUnlock()
    }

    proxy.ModifyResponse = func(resp *http.Response) error {
        return nil
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
        log.Fatal("Environment variables NCORE_USERNAME and NCORE_PASSWORD are required")
    }

    if err := loginToNCore(username, password); err != nil {
        log.Fatalf("Login failed: %v", err)
    }

    http.HandleFunc("/", proxyHandler)

    log.Println("nCore proxy running on http://localhost:8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
