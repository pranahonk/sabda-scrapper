package services

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

// AuthService handles JWT authentication
type AuthService struct {
	secretKey  string
	expiration time.Duration
	apiKeys    map[string]string
}

// NewAuthService creates a new authentication service
func NewAuthService(secretKey string, expiration time.Duration, apiKeys map[string]string) *AuthService {
	return &AuthService{
		secretKey:  secretKey,
		expiration: expiration,
		apiKeys:    apiKeys,
	}
}

// GenerateToken generates a JWT token for the given API key
func (a *AuthService) GenerateToken(apiKey string) (string, time.Time, error) {
	// Validate API key
	if !a.isValidAPIKey(apiKey) {
		return "", time.Time{}, fmt.Errorf("invalid API key")
	}

	// Create token claims
	now := time.Now()
	expiresAt := now.Add(a.expiration)

	claims := jwt.MapClaims{
		"api_key": a.hashAPIKey(apiKey),
		"exp":     expiresAt.Unix(),
		"iat":     now.Unix(),
	}

	// Create token
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString([]byte(a.secretKey))
	if err != nil {
		return "", time.Time{}, fmt.Errorf("failed to sign token: %w", err)
	}

	return tokenString, expiresAt, nil
}

// VerifyToken verifies and parses a JWT token
func (a *AuthService) VerifyToken(tokenString string) (*jwt.MapClaims, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		// Validate signing method
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(a.secretKey), nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to parse token: %w", err)
	}

	if !token.Valid {
		return nil, fmt.Errorf("invalid token")
	}

	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok {
		return nil, fmt.Errorf("invalid token claims")
	}

	return &claims, nil
}

// IsValidAPIKey checks if the provided API key is valid
func (a *AuthService) IsValidAPIKey(apiKey string) bool {
	return a.isValidAPIKey(apiKey)
}

func (a *AuthService) isValidAPIKey(apiKey string) bool {
	for _, validKey := range a.apiKeys {
		if apiKey == validKey {
			return true
		}
	}
	return false
}

func (a *AuthService) hashAPIKey(apiKey string) string {
	hash := sha256.Sum256([]byte(apiKey))
	return hex.EncodeToString(hash[:])
}