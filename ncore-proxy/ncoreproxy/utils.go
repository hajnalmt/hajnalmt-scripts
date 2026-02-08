package ncoreproxy

import (
	"bytes"
	"compress/gzip"
	"io"
	"net/http"
	"strconv"
	"strings"
)

func rewriteResponse(tag string) func(*http.Response) error {
	return func(resp *http.Response) error {
		contentType := resp.Header.Get("Content-Type")
		shouldRewrite := strings.Contains(contentType, "html") || strings.Contains(contentType, "javascript") || strings.Contains(contentType, "css")

		if !shouldRewrite {
			return nil
		}

		var body []byte
		var err error

		if resp.Header.Get("Content-Encoding") == "gzip" {
			gzReader, err := gzip.NewReader(resp.Body)
			if err != nil {
				return err
			}
			body, err = io.ReadAll(gzReader)
			resp.Body.Close()
			gzReader.Close()
			resp.Header.Del("Content-Encoding")
			if err != nil {
				return err
			}
		} else {
			body, err = io.ReadAll(resp.Body)
			resp.Body.Close()
		}
		if err != nil {
			return err
		}

		// Replace all variations of static.ncore.pro URLs
		modified := bytes.ReplaceAll(body, []byte("https://static.ncore.pro"), []byte("/proxy-static"))
		modified = bytes.ReplaceAll(modified, []byte("http://static.ncore.pro"), []byte("/proxy-static"))
		modified = bytes.ReplaceAll(modified, []byte("//static.ncore.pro"), []byte("/proxy-static"))

		// Special handling for CSS/JS files from StaticProxy
		// These files contain absolute paths like url(/styles/...) or "/static/..."
		// which the browser will resolve relative to localhost:8080
		// We need to prefix them with /proxy-static so they go through our proxy
		if tag == "StaticProxy" && (strings.Contains(contentType, "css") || strings.Contains(contentType, "javascript")) {
			// For CSS: url(/styles/...) → url(/proxy-static/styles/...)
			modified = bytes.ReplaceAll(modified, []byte("url(/styles/"), []byte("url(/proxy-static/styles/"))
			modified = bytes.ReplaceAll(modified, []byte("url('/styles/"), []byte("url('/proxy-static/styles/"))
			modified = bytes.ReplaceAll(modified, []byte(`url("/styles/`), []byte(`url("/proxy-static/styles/`))

			// For CSS: url(/static/...) → url(/proxy-static/static/...)
			modified = bytes.ReplaceAll(modified, []byte("url(/static/"), []byte("url(/proxy-static/static/"))
			modified = bytes.ReplaceAll(modified, []byte("url('/static/"), []byte("url('/proxy-static/static/"))
			modified = bytes.ReplaceAll(modified, []byte(`url("/static/`), []byte(`url("/proxy-static/static/`))

			// For JS: "/static/..." or '/static/...'
			modified = bytes.ReplaceAll(modified, []byte(`"/static/`), []byte(`"/proxy-static/static/`))
			modified = bytes.ReplaceAll(modified, []byte(`'/static/`), []byte(`'/proxy-static/static/`))
			modified = bytes.ReplaceAll(modified, []byte(`"/styles/`), []byte(`"/proxy-static/styles/`))
			modified = bytes.ReplaceAll(modified, []byte(`'/styles/`), []byte(`'/proxy-static/styles/`))
		}

		resp.Body = io.NopCloser(bytes.NewReader(modified))
		resp.ContentLength = int64(len(modified))
		resp.Header.Set("Content-Length", strconv.Itoa(len(modified)))

		if loc := resp.Header.Get("Location"); strings.HasPrefix(loc, baseURL) {
			resp.Header.Set("Location", strings.Replace(loc, baseURL, "http://localhost:8080", 1))
		}

		return nil
	}
}
