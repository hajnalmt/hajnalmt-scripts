package ncoreproxy

import (
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"
)

var staticOrigin = "https://static.ncore.pro"

func MainProxy(client *http.Client) *httputil.ReverseProxy {
	ncoreURL, _ := url.Parse(baseURL)

	return &httputil.ReverseProxy{
		Director: func(req *http.Request) {
			req.URL.Scheme = ncoreURL.Scheme
			req.URL.Host = ncoreURL.Host
			req.Host = ncoreURL.Host
			req.Header.Set("User-Agent", "Mozilla/5.0")
			for _, c := range client.Jar.Cookies(ncoreURL) {
				req.AddCookie(c)
			}
		},
		ModifyResponse: rewriteResponse("MainProxy"),
	}
}

func StaticProxy() *httputil.ReverseProxy {
	staticURL, _ := url.Parse(staticOrigin)

	return &httputil.ReverseProxy{
		Director: func(req *http.Request) {
			req.URL.Scheme = staticURL.Scheme
			req.URL.Host = staticURL.Host
			req.Host = staticURL.Host
			req.URL.Path = strings.TrimPrefix(req.URL.Path, "/proxy-static")
			req.Header.Set("Referer", baseURL+"/")
			req.Header.Set("User-Agent", "Mozilla/5.0")
		},
		ModifyResponse: rewriteResponse("StaticProxy"),
	}
}
