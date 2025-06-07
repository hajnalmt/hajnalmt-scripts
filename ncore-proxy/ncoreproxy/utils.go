package ncoreproxy

import (
	"bytes"
	"compress/gzip"
	"io"
	"log"
	"net/http"
	"strconv"
	"strings"
)

func rewriteResponse(tag string) func(*http.Response) error {
	return func(resp *http.Response) error {
		contentType := resp.Header.Get("Content-Type")
		if !(strings.Contains(contentType, "html") || strings.Contains(contentType, "javascript") || strings.Contains(contentType, "css")) {
			return nil
		}

		var body []byte
		var err error

		if resp.Header.Get("Content-Encoding") == "gzip" {
			log.Printf("📦 %s: gzip-encoded %s", tag, resp.Request.URL)
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

		modified := bytes.ReplaceAll(body, []byte(staticOrigin), []byte("/proxy-static"))
		if !bytes.Equal(body, modified) {
			log.Printf("🔁 %s rewrote content in %s", tag, resp.Request.URL.Path)
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
