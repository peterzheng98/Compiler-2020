package main

import (
	"encoding/json"
	"net/http"
)

func fetchServerStatus(w http.ResponseWriter, r *http.Request) {
	var sendMessage = make(map[string]string)
	compileMessage, err1 := json.Marshal(compilePool)
	semanticMessage, err2 := json.Marshal(semanticPool)
	codegenMessage, err3 := json.Marshal(codegenPool)
	optimizeMessage, err4 := json.Marshal(optimizePool)
	sendMessage["compile"] = string(compileMessage)
	sendMessage["semantic"] = string(semanticMessage)
	sendMessage["codegen"] = string(codegenMessage)
	sendMessage["optimize"] = string(optimizeMessage)
	if err1 != nil{
		sendMessage["error-compile"] = err1.Error()
	}
	if err2 != nil{
		sendMessage["error-semantic"] = err2.Error()
	}
	if err3 != nil{
		sendMessage["error-codegen"] = err3.Error()
	}
	if err4 != nil{
		sendMessage["error-optimize"] = err4.Error()
	}
	_ = json.NewEncoder(w).Encode(sendFormat{
		Code:    200,
		Message: sendMessage,
	})
}
