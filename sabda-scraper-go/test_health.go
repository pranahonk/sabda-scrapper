package main

import (
	"fmt"
	"net/http"
	"time"
)

func main() {
	// Wait for server to start
	time.Sleep(2 * time.Second)

	// Test health endpoint
	resp, err := http.Get("http://localhost:5000/api/health")
	if err != nil {
		fmt.Printf("Health check failed: %v\n", err)
		return
	}
	defer resp.Body.Close()

	fmt.Printf("Health check status: %d\n", resp.StatusCode)
	
	if resp.StatusCode == 200 {
		fmt.Println("✅ Health check passed!")
	} else {
		fmt.Println("❌ Health check failed!")
	}
}