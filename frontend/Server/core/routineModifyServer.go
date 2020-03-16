package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

func modifyServer(w http.ResponseWriter, r *http.Request) {
	var operation sendFormatWeb
	err := json.NewDecoder(r.Body).Decode(&operation)
	if err != nil {
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    400,
			Message: fmt.Sprintf("Error: %s", err.Error()),
		})
		return
	}
	// validate key
	if len(operation.Message["passkey"]) == 0 || operation.Message["passkey"][0] != secretKey {
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    403,
			Message: fmt.Sprintf("Forbidden: Private key not matched"),
		})
		return
	}
	// check all clean
	if len(operation.Message["all"]) != 0 {
		semanticPool = make([]JudgePoolElement, 0)
		codegenPool = make([]JudgePoolElement, 0)
		optimizePool = make([]JudgePoolElement, 0)
		compilePool = make(map[string]JudgePoolElement)
		_ = json.NewEncoder(w).Encode(simpleSendFormat{
			Code:    200,
			Message: fmt.Sprintf("All cleared."),
		})
		return
	}
	// clean compile
	if len(operation.Message["compile"]) != 0{
		for _, v := range operation.Message["compile"]{
			if _, ok := compilePool[v]; ok {
				delete(compilePool, v)
			}
		}
	}
	// clear semantic
	if len(operation.Message["semantic"]) != 0{
		semanticPool = make([]JudgePoolElement, 0)
	}
	if len(operation.Message["codegen"]) != 0{
		codegenPool = make([]JudgePoolElement, 0)
	}
	if len(operation.Message["optimize"]) != 0{
		optimizePool = make([]JudgePoolElement, 0)
	}
	_ = json.NewEncoder(w).Encode(simpleSendFormat{
		Code:    200,
		Message: "Ok, Done.",
	})
}
